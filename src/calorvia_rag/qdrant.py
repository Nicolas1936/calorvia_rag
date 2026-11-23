from calorvia_rag.config import settings

from qdrant_client import QdrantClient

def get_qdrant_client():
    return QdrantClient(
        url = settings.qdrant_url,
        api_key=settings.qdrant_api_key
    )

def get_collection_name(embedder_name, chunk_type, chunk_size, sparse_vector=None, context_line=False, sparse_language=None, excel_reader=None,
                        include_images=False, include_scans=False, scan_reader=False):
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
    return name.replace('/', '-')
