from calorvia_rag.config import settings, runner_settings
from calorvia_rag.db import list_documents_to_chunk
from calorvia_rag.etl.inventory import detect_language
from calorvia_rag.etl.excel import workbook_texts

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

def iter_chunks(chunker):
    """Tous les chunks du corpus, document par document, dans l'ordre du registre."""
    chunking_cfg = runner_settings['chunking']
    context_line = chunking_cfg['context_line']
    excel_reader = chunking_cfg.get('excel_reader', 'docling')
    for row in list_documents_to_chunk():
        if row['format'] == 'xlsx' and excel_reader == 'openpyxl':
            yield from chunk_workbook(row, context_line)
        else:
            yield from chunk_document(row, chunker, context_line)

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