from calorvia_rag.config import settings, runner_settings
from calorvia_rag.db import list_documents_to_chunk, list_documents_to_transcribe, list_scans_to_convert
from calorvia_rag.etl.inventory import detect_language
from calorvia_rag.etl.excel import workbook_texts
from calorvia_rag.etl.vision import get_vlm_client, document_pages, transcribe_cached, pdf_images

from transformers import AutoTokenizer
from docling_core.types.doc import DoclingDocument
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from docling_core.transforms.chunker.hierarchical_chunker import HierarchicalChunker
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer

from pathlib import Path

from pathlib import Path

CHUNKERS = {
    'hybrid': HybridChunker,
    'hierarchical': HierarchicalChunker
}

def get_chunker(chunker_type, embedder_name, max_tokens):
    tokenizer = HuggingFaceTokenizer(
        tokenizer=AutoTokenizer.from_pretrained((Path(settings.models_folder) / 'embedder' / embedder_name)),
        max_tokens=max_tokens
    )
    chunker = CHUNKERS.get(chunker_type)(tokenizer=tokenizer)
    return chunker

def chunk_document(row, chunker, context_line):
    """Découpe un export Docling. `row` est la ligne du registre du document."""
    document = DoclingDocument.load_from_json(settings.processed_documents_folder / f"{row['sha256']}.json")

    for i, chunk in enumerate(chunker.chunk(dl_doc = document)):
        text = chunker.contextualize(chunk)          # titres de section + texte du chunk
        if context_line:
            text = row['context_line'] + '\n' + text

        yield {
            'document': row['path'],                 # chemin relatif : c'est l'identité du document
            'chunk_index': i,
            'headings': ' | '.join(chunk.meta.headings or []),
            'text': text,
            'language': detect_language(chunk.text, default = row['language'] or 'fr'),
            **document_metadata(row)
        }

def chunk_workbook(row, context_line):
    """Découpe un classeur lu par openpyxl (etl/excel.py) : une phrase par ligne de tableau."""
    path = settings.corpus_folder / row['path']
    for i, (text, headings, sheet, row_number) in enumerate(workbook_texts(path)):
        yield {
            'document': row['path'],
            'chunk_index': i,
            'headings': headings,
            'text': row['context_line'] + '\n' + text if context_line else text,
            'language': row['language'] or 'fr',     # langue du classeur : une ligne de nombres se détecte mal
            'sheet': sheet,
            'row': row_number,
            **document_metadata(row),
        }

def pack_paragraphs(text, prefix, tokenizer, max_tokens):
    """Paragraphes (séparés par une ligne vide) regroupés en morceaux de max_tokens au plus, préfixe compris.
    Un tableau Markdown forme un seul paragraphe : il n'est jamais coupé, contrairement à Docling qui le
    relit en triplets et associe mal les colonnes d'un organigramme."""
    parts, current = [], ''
    for paragraph in (p.strip() for p in text.split('\n\n')):
        if paragraph in ('', '***', '---'):                 # lignes de séparation du VLM : rien à chercher
            continue
        candidate = f'{current}\n\n{paragraph}' if current else paragraph
        if current and tokenizer.count_tokens(f'{prefix}\n{candidate}') > max_tokens:
            parts.append(current)
            current = paragraph
        else:
            current = candidate
    return parts + [current] if current else parts

def chunk_transcription(row, chunker, context_line, vlm_client):
    """Découpe la transcription par le VLM (etl/vision.py) d'une image ou des pages d'un scan :
    la page entière si elle tient dans max_tokens, sinon des paragraphes regroupés.
    Le payload garde le chemin de l'image et la page, pour l'afficher sous la réponse."""
    pages = document_pages(row)
    stem = Path(row['path']).stem
    i = 0
    for page in pages:
        text = transcribe_cached(row, page, vlm_client)['text']     # le cache évite de rappeler le VLM
        if page is None:
            header = f"Transcription de l'image « {stem} »"
        else:
            header = f"Transcription du scan « {stem} », page {page + 1} sur {len(pages)}"
        prefix = f"{row['context_line']}\n{header}" if context_line else header
        for part in pack_paragraphs(text, prefix, chunker.tokenizer, chunker.max_tokens):
            yield {
                'document': row['path'],
                'chunk_index': i,
                'headings': '',
                'text': f'{prefix}\n{part}',
                'language': detect_language(part, default = row['language'] or 'fr'),
                'image_path': row['path'],
                'page': page,                                    # à partir de 0, comme page_image() ; None pour une image
                **document_metadata(row),
            }
            i += 1

def chunk_pdf_images(row, chunker, context_line, vlm_client, first_index):
    """Les graphiques insérés dans un PDF texte, transcrits par le VLM (cache, etl/vision.py).
    Numérotés après les chunks Docling du document : l'identifiant d'un point dépend de document et chunk_index."""
    stem = Path(row['path']).stem
    i = first_index
    for page, index, image in pdf_images(settings.corpus_folder / row['path']):
        text = transcribe_cached(row, page, vlm_client, index = index, image = image)['text']
        header = f"Graphique du document « {stem} », page {page + 1}"
        prefix = f"{row['context_line']}\n{header}" if context_line else header
        for part in pack_paragraphs(text, prefix, chunker.tokenizer, chunker.max_tokens):
            yield {
                'document': row['path'],
                'chunk_index': i,
                'headings': '',
                'text': f'{prefix}\n{part}',
                'language': detect_language(part, default = row['language'] or 'fr'),
                'image_path': row['path'],
                'page': page,
                **document_metadata(row),
            }
            i += 1

def vision_source_types():
    """Les types de documents à faire lire par le VLM, selon la section [corpus] du TOML."""
    corpus_cfg = runner_settings.get('corpus', {})
    return {source_type for source_type, key in (('image', 'include_images'), ('scan', 'include_scanned_pdfs'))
            if corpus_cfg.get(key)}

def iter_chunks(chunker):
    """Tous les chunks du corpus, document par document, dans l'ordre du registre ; puis les images et les scans."""
    chunking_cfg = runner_settings['chunking']
    corpus_cfg = runner_settings.get('corpus', {})
    context_line = chunking_cfg['context_line']
    excel_reader = chunking_cfg.get('excel_reader', 'docling')
    vlm_client = get_vlm_client()             # aucun appel au VLM tant que les transcriptions sont dans le cache

    for row in list_documents_to_chunk():
        if row['format'] == 'xlsx' and excel_reader == 'openpyxl':
            yield from chunk_workbook(row, context_line)
            continue
        chunks = list(chunk_document(row, chunker, context_line))
        yield from chunks
        if row['format'] == 'pdf' and corpus_cfg.get('include_pdf_images'):
            yield from chunk_pdf_images(row, chunker, context_line, vlm_client, first_index = len(chunks))

    source_types = vision_source_types()
    scan_reader = corpus_cfg.get('scan_reader', 'vlm')
    ocr_hashes = {sha256 for _, sha256 in list_scans_to_convert()} if scan_reader == 'docling' else set()
    for row in list_documents_to_transcribe():
        if row['source_type'] not in source_types:       # image ou scan exclu par le TOML : on passe
            continue
        if row['sha256'] in ocr_hashes:                  # document numérisé : export Docling avec OCR
            yield from chunk_document(row, chunker, context_line)
        else:                                            # transcription du VLM (cache)
            yield from chunk_transcription(row, chunker, context_line, vlm_client)

def documents_without_export():
    """Les documents que iter_chunks lirait dans un export Docling absent : conversion en échec ou pas encore faite.
    Suit les mêmes règles que iter_chunks : un classeur lu par openpyxl n'a pas besoin d'export."""
    chunking_cfg = runner_settings['chunking']
    corpus_cfg = runner_settings.get('corpus', {})
    excel_by_openpyxl = chunking_cfg.get('excel_reader', 'docling') == 'openpyxl'
    rows = [row for row in list_documents_to_chunk() if not (row['format'] == 'xlsx' and excel_by_openpyxl)]
    if corpus_cfg.get('scan_reader', 'vlm') == 'docling':
        ocr_hashes = {sha256 for _, sha256 in list_scans_to_convert()}
        rows += [row for row in list_documents_to_transcribe()
                 if row['source_type'] in vision_source_types() and row['sha256'] in ocr_hashes]
    return [row['path'] for row in rows if not (settings.processed_documents_folder / f"{row['sha256']}.json").exists()]

def document_metadata(row):
    """Les métadonnées du registre, communes à tous les chunks d'un document."""
    return {
        'format': row['format'],
        'department': row['department'],
        'doc_type': row['doc_type'],
        'doc_date': row['doc_date'].isoformat() if row['doc_date'] else None,
        'period': row['period'],
        'version': row['version'],
        'status': row['status'],
        'source_type': row['source_type'],
    }

if  __name__ == '__main__':
    from collections import Counter

    chunking = runner_settings['chunking']
    chunker = get_chunker(chunking['type'], runner_settings['embedder']['model'], chunking['max_tokens'])
    chunks = list(iter_chunks(chunker))

    print(runner_settings['name'], '- context_line =', chunking['context_line'])
    print(len(chunks), 'chunks')
    print('Formats:  ', Counter(c['format'] for c in chunks))
    print('Languages:', Counter(c['language'] for c in chunks))
    print(chunks[0]['text'][:300])