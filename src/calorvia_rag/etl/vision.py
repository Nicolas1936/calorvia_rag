"""Transcription des images et des PDF scannés par le VLM, une seule fois, avec un cache (section 6)."""
from calorvia_rag.config import settings
from calorvia_rag.db import list_documents_to_transcribe

from openai import OpenAI
from PIL import Image
import base64
import io
import time
import pymupdf
import hashlib, json


TRANSCRIBE_PROMPT = """Tu transcris des documents d'entreprise pour un moteur de recherche.
1. Recopie tout le texte visible, exactement comme il est écrit : nombres, codes, dates, unités et
   annotations manuscrites compris. Rends les tableaux en Markdown.
2. Puis, sous le titre « Description », décris en trois phrases au plus le type d'image (organigramme,
   plan, graphique, photo, facture...) et ce qu'elle montre qui n'est pas écrit : les rattachements
   d'un organigramme, la valeur la plus haute d'un graphique, la position des éléments d'un plan.
N'invente rien : si un élément est illisible, écris [illisible]."""

def get_vlm_client():
    return OpenAI(base_url = settings.llm_url, api_key = settings.llm_server_api_key)

def image_to_data_url(image, max_side = 1600):
    """Image PIL réduite si besoin, en URL « data: » JPEG base64, acceptée par l'API OpenAI."""
    image = image.convert('RGB')
    image.thumbnail((max_side, max_side))
    buffer = io.BytesIO()
    image.save(buffer, format = 'JPEG', quality = 90)
    return 'data:image/jpeg;base64,' + base64.b64encode(buffer.getvalue()).decode()

def page_image(path, page, dpi = 150):
    """Une page de PDF en image PIL."""
    with pymupdf.open(path) as pdf:
        pixmap = pdf[page].get_pixmap(dpi = dpi)
    return Image.open(io.BytesIO(pixmap.tobytes('png')))

def describe_image(image, vlm_client, prompt = TRANSCRIBE_PROMPT, max_tokens = 2500):
    """Transcription et description d'une image par le VLM (température 0)."""
    response = vlm_client.chat.completions.create(
        model = settings.vision_model, temperature = 0, max_tokens = max_tokens,
        messages = [{'role': 'user', 'content': [
            {'type': 'text', 'text': prompt},
            {'type': 'image_url', 'image_url': {'url': image_to_data_url(image)}},
        ]}],
    )
    choice = response.choices[0]
    if choice.finish_reason == 'length':                 # coupée par max_tokens : à repérer dans le cache
        return choice.message.content + '\n[transcription tronquée]'
    return choice.message.content

def cache_path(sha256, page, prompt):
    """Fichier du cache : empreinte du fichier, page, modèle et prompt (changer de prompt relance la transcription)."""
    key = hashlib.sha256(f'{sha256}|{page}|{settings.vision_model}|{prompt}'.encode()).hexdigest()[:16]
    return settings.vision_folder / f'{key}.json'

def transcribe_cached(row, page, vlm_client, prompt = TRANSCRIBE_PROMPT):
    """Transcription d'une image (page None) ou d'une page de scan, calculée une seule fois."""
    cache = cache_path(row['sha256'], page, prompt)
    if cache.exists():
        return json.loads(cache.read_text(encoding = 'utf-8'))
    path = settings.corpus_folder / row['path']
    image = page_image(path, page) if page is not None else Image.open(path)
    started = time.perf_counter()
    text = describe_image(image, vlm_client, prompt)
    record = {'path': row['path'], 'sha256': row['sha256'], 'page': page, 'model': settings.vision_model,
              'prompt': prompt, 'seconds': round(time.perf_counter() - started, 1), 'text': text}
    settings.vision_folder.mkdir(parents = True, exist_ok = True)
    cache.write_text(json.dumps(record, ensure_ascii = False, indent = 2), encoding = 'utf-8')
    return record

def document_pages(row):
    """Pages à transcrire : [None] pour une image, [0, 1, …] pour un PDF scanné."""
    if row['source_type'] != 'scan':
        return [None]
    with pymupdf.open(settings.corpus_folder / row['path']) as pdf:
        return list(range(len(pdf)))

def transcribe_corpus():
    """Transcrit toutes les images et toutes les pages des scans ; le temps total compte aussi celles du cache."""
    vlm_client = get_vlm_client()
    total = 0
    for row in list_documents_to_transcribe():
        for page in document_pages(row):
            record = transcribe_cached(row, page, vlm_client)
            total += record['seconds']
            print(f"{record['seconds']:6.1f} s  {row['path']}" + (f' (page {page + 1})' if page is not None else ''))
    print(f'Temps total de transcription : {total / 60:.1f} min')

if __name__ == '__main__':
    transcribe_corpus()
