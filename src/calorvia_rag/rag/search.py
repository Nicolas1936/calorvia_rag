from calorvia_rag.config import runner_settings
from calorvia_rag.embedding import get_embedder, get_sparse_options, get_query_text, embed, embed_sparse
from calorvia_rag.qdrant import get_qdrant_client, get_collection_name

from qdrant_client import models
import threading


def dense_search(dense_vector, collection_name, qdrant_client, limit, query_filter = None):
    return qdrant_client.query_points(
        collection_name, query = dense_vector, using = 'dense',
        limit = limit, query_filter = query_filter
    ).points

def sparse_search(sparse_query, collection_name, qdrant_client, limit, query_filter = None):
    return qdrant_client.query_points(
        collection_name, query = sparse_query, using = 'sparse',
        limit = limit, query_filter = query_filter
    ).points

def hybrid_search(dense_vectors, sparse_queries, collection_name, qdrant_client, limit, query_filter = None):
    """Une liste dense et une liste BM25 par version de la question, toutes fusionnées par RRF."""
    prefetch = [models.Prefetch(query = vector, using = 'dense', limit = limit) for vector in dense_vectors]
    prefetch += [models.Prefetch(query = sparse_query, using = 'sparse', limit = limit) for sparse_query in sparse_queries]
    
    return qdrant_client.query_points(
        collection_name,
        prefetch = prefetch,
        query = models.RrfQuery(rrf = models.Rrf(k = 60)),
        limit = limit, query_filter = query_filter
    ).points

def search_chunks(query, qdrant_client, embedder, query_filter = None, translations = None):
    embedder_cfg = runner_settings['embedder']
    chunking_cfg = runner_settings['chunking']
    index_cfg = runner_settings['index']
    search_cfg = runner_settings['search']

    collection_name = get_collection_name(
        embedder_name = embedder_cfg['model'],
        chunk_type = chunking_cfg['type'],
        chunk_size = chunking_cfg['max_tokens'],
        sparse_vector = index_cfg.get('sparse_vector'),
        context_line = chunking_cfg['context_line'],
        sparse_language = index_cfg.get('sparse_language'),
        excel_reader = chunking_cfg.get('excel_reader'),
        include_images = runner_settings.get('corpus', {}).get('include_images'),
        include_scans = runner_settings.get('corpus', {}).get('include_scanned_pdfs'),
    )
    limit = search_cfg['candidates']

    if search_cfg['method'] == 'dense':
        dense_vector = embed([get_query_text(query, embedder_cfg)], embedder, embedder_cfg['model'])[0]
        return dense_search(dense_vector, collection_name, qdrant_client, limit, query_filter)

    if search_cfg['method'] == 'sparse':
        sparse_query = embed_sparse(query, get_sparse_options(index_cfg))
        return sparse_search(sparse_query, collection_name, qdrant_client, limit, query_filter)

    # Recherche hybride : une liste dense et une liste BM25 par version de la question
    translations = translations or {'fr': query}      # sans traduction : la question seule, en français
    texts = [get_query_text(text, embedder_cfg) for text in translations.values()]

    dense_vectors = embed(texts, embedder, embedder_cfg['model'])          # un seul appel pour 1 ou 3 langues
    sparse_queries = [embed_sparse(text, get_sparse_options(index_cfg, language))
                      for language, text in translations.items()]           # chaque langue avec son stemme
    
    return hybrid_search(dense_vectors, sparse_queries, collection_name, qdrant_client, limit, query_filter)


_search_lock = threading.Lock()

def search_and_filter_chunks(query, qdrant_client, embedder, query_filter = None, translations = None):
    with _search_lock:
        points = search_chunks(query, qdrant_client, embedder, query_filter, translations)
        if not points and query_filter:
            points = search_chunks(query, qdrant_client, embedder, translations=translations)
        return points


if __name__ == '__main__':
    points = search_and_filter_chunks(
        "Quelle vitesse est autorisée dans l'entrepôt de Gand ?",
        get_qdrant_client(), get_embedder()
    )
    for point in points:
        print(round(point.score, 3), point.payload['document'], point.payload['chunk_index'])
