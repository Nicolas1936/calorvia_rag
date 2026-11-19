from calorvia_rag.config import settings, runner_settings

import requests as rq

def rerank_chunks(query, chunks):
    reranker_cfg = runner_settings['reranker']
    payload = {
        'model': reranker_cfg['model'],
        'query': query,
        'documents': [chunk.payload['text'] for chunk in chunks],
        'top_n': reranker_cfg['top_k']
    }

    r = rq.post(settings.rerank_url, json = payload)
    r.raise_for_status()
    return [(chunks[result['index']], result['relevance_score']) for result in r.json()['results']]


if __name__ == '__main__':
    from calorvia_rag.embedding import get_embedder
    from calorvia_rag.qdrant import get_qdrant_client
    from calorvia_rag.rag.search import search_and_filter_chunks

    query = "Quelle vitesse est autorisée dans l'entrepôt de Gand ?"
    points = search_and_filter_chunks(query, get_qdrant_client(), get_embedder())

    print('--- search ---')
    for i, point in enumerate(points):
        print(i, round(point.score, 3), point.payload['document'], point.payload['chunk_index'])

    print('--- rerank ---')
    for chunk, score in rerank_chunks(query, points):
        print(points.index(chunk), round(score, 3), chunk.payload['document'], chunk.payload['chunk_index'])
