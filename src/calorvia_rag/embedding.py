from calorvia_rag.config import settings

from openai import OpenAI
from qdrant_client import models

STEMMERS = {'fr': 'french', 'nl': 'dutch', 'en': 'english'}

def get_embedder():
    return OpenAI(
        base_url = settings.embedding_url,
        api_key = settings.llm_server_api_key
    )

def get_stemmer(language):
    """Code de langue (fr, nl, en…) → stemmer BM25 de Qdrant ; langue du corpus si inconnu ou None."""
    return STEMMERS.get(language, settings.corpus_language)

def get_sparse_options(index_cfg, language = None):
    return {
        'language': get_stemmer(language),
        'ascii_folding': index_cfg['sparse_embedder_ascii_folding'],
    }

def get_query_text(query, embedder_cfg):
    if embedder_cfg['query_instruction']:
        return f"Instruct: {embedder_cfg['query_instruction']}\nQuery: {query}"
    return query

def embed(chunks, embedder, model_name):
    response = embedder.embeddings.create(model=model_name, input=chunks)
    return [item.embedding for item in response.data]

def embed_sparse(text, options):
    return models.Document(text=text, model='qdrant/bm25', options=options)
