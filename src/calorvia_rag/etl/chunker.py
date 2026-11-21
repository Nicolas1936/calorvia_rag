from calorvia_rag.config import settings, runner_settings
from calorvia_rag.db import list_documents_to_chunk, list_documents_to_transcribe
from calorvia_rag.etl.inventory import detect_language
from calorvia_rag.etl.excel import workbook_texts
from calorvia_rag.etl.vision import get_vlm_client, document_pages, transcribe_cached

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

def vision_source_types():
    """Les types de documents à faire lire par le VLM, selon la section [corpus] du TOML."""
    corpus_cfg = runner_settings.get('corpus', {})
    return {source_type for source_type, key in (('image', 'include_images'), ('scan', 'include_scanned_pdfs'))
            if corpus_cfg.get(key)}

def iter_chunks(chunker):
    """Tous les chunks du corpus, document par document, dans l'ordre du registre ; puis les images et les scans."""
    chunking_cfg = runner_settings['chunking']
    context_line = chunking_cfg['context_line']
    excel_reader = chunking_cfg.get('excel_reader', 'docling')
    for row in list_documents_to_chunk():
        if row['format'] == 'xlsx' and excel_reader == 'openpyxl':
            yield from chunk_workbook(row, context_line)
        else:
            yield from chunk_document(row, chunker, context_line)

    source_types = vision_source_types()
    if source_types:
        vlm_client = get_vlm_client()
        for row in list_documents_to_transcribe():
            if row['source_type'] in source_types:
                yield from chunk_transcription(row, chunker, context_line, vlm_client)

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