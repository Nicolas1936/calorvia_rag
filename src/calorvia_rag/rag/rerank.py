from calorvia_rag.config import settings, runner_settings

import requests as rq

def call_reranker(query, chunks, top_n):
    if not chunks:              # recherche vide (collection vide) : le reranker refuserait une liste vide (400)
        return []
    payload = {
        'model': runner_settings['reranker']['model'],
        'query': query,
        'documents': [chunk.payload['text'] for chunk in chunks],
        'top_n': top_n,
    }
    r = rq.post(settings.rerank_url, json = payload)
    r.raise_for_status()
    return [(chunks[result['index']], result['relevance_score']) for result in r.json()['results']]

def rerank_chunks(query, chunks, translations = None):
    reranker_cfg = runner_settings['reranker']
    if not (reranker_cfg.get('per_language') and translations):
        return call_reranker(query, chunks, reranker_cfg['top_k'])          # comme avant

    groups = {}                                                             # question → passages de sa langue
    for chunk in chunks:
        question = translations.get(chunk.payload['language'], query)       # langue sans traduction → question fr
        groups.setdefault(question, []).append(chunk)

    scored = [pair for question, group in groups.items() for pair in call_reranker(question, group, len(group))]
    return sorted(scored, key = lambda pair: pair[1], reverse = True)[:reranker_cfg['top_k']]


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
