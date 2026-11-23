from calorvia_rag.config import settings, runner_settings

from qdrant_client import QdrantClient

def get_qdrant_client():
    return QdrantClient(
        url = settings.qdrant_url,
        api_key=settings.qdrant_api_key
    )

def get_collection_name(embedder_name, chunk_type, chunk_size, sparse_vector=None, context_line=False, sparse_language=None, excel_reader=None,
                        include_images=False, include_scans=False, scan_reader=False, include_pdf_images=False):
    name = f'{embedder_name}_{chunk_type}_{chunk_size}'
    if context_line:
        name += '_ctx'
    if sparse_vector:
        name += f'_{sparse_vector}'
        if sparse_language == 'per_chunk':
            name += '_lang'
    if excel_reader == 'openpyxl':
        name += '_xlsx'
    if include_images:
        name += '_img'
    if include_scans:
        name += '_scan'
    if scan_reader == 'docling':
        name += '_ocr'
    if include_pdf_images:
        name += '_pdfimg'
    return name.replace('/', '-')

def get_current_collection_name():
    """La collection de la configuration courante (le TOML de RUNNER_CONFIG_PATH) : la même pour l'index, la recherche et le runner."""
    embedder_cfg = runner_settings['embedder']
    chunking_cfg = runner_settings['chunking']
    index_cfg = runner_settings['index']
    corpus_cfg = runner_settings.get('corpus', {})
    return get_collection_name(
        embedder_name = embedder_cfg['model'],
        chunk_type = chunking_cfg['type'],
        chunk_size = chunking_cfg['max_tokens'],
        sparse_vector = index_cfg.get('sparse_vector'),
        context_line = chunking_cfg['context_line'],
        sparse_language = index_cfg.get('sparse_language'),
        excel_reader = chunking_cfg.get('excel_reader'),
        include_images = corpus_cfg.get('include_images'),
        include_scans = corpus_cfg.get('include_scanned_pdfs'),
        scan_reader = corpus_cfg.get('scan_reader'),
        include_pdf_images = corpus_cfg.get('include_pdf_images'),
    )
