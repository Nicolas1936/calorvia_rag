import numpy as np

from calorvia_rag.config import runner_settings
from calorvia_rag.etl.convert import convert_corpus
from calorvia_rag.etl.chunker import iter_chunks, get_chunker
from calorvia_rag.embedding import get_embedder, get_sparse_options, embed, embed_sparse, get_stemmer
from calorvia_rag.qdrant import get_qdrant_client, get_collection_name

from qdrant_client import models

import uuid
from itertools import batched

KEYWORD_FIELDS = ('document', 'doc_type', 'status', 'department', 'language')

def init_collection(qdrant_client, collection_name, vector_size):
    if qdrant_client.collection_exists(collection_name):
        qdrant_client.delete_collection(collection_name)   # on repart de zéro : pas de vieux chunks

    qdrant_client.create_collection(
        collection_name,
        vectors_config = {
            'dense': models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
        },
        sparse_vectors_config = {
            'sparse': models.SparseVectorParams(modifier=models.Modifier.IDF),
        },
    )

    for field in KEYWORD_FIELDS:
        qdrant_client.create_payload_index(
            collection_name, 
            field_name=field, 
            field_schema=models.PayloadSchemaType.KEYWORD,
        )

    qdrant_client.create_payload_index(
        collection_name,
        field_name='doc_date',
        field_schema=models.PayloadSchemaType.DATETIME,
    )

def get_chunk_uuid(chunk):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{chunk['document']}/{chunk['chunk_index']}"))

def iter_points(chunker, embedder, model_name, embedding_batch_size, sparse_embedder_options, per_language):
    chunks = iter_chunks(chunker)
    for batch in batched(chunks, embedding_batch_size):
        dense_vectors = embed([chunk['text'] for chunk in batch], embedder, model_name)
        for chunk, dense_vector in zip(batch, dense_vectors):
            sparse_options = sparse_embedder_options
            if per_language:
                sparse_options = {**sparse_embedder_options, 'language': get_stemmer(chunk['language'])}
            yield models.PointStruct(
                id=get_chunk_uuid(chunk),
                vector = {
                    'dense': dense_vector,
                    'sparse': embed_sparse(chunk['text'], sparse_options)
                }
                , payload = chunk
            )

def probe_avg_len(chunker):
    """Longueur moyenne d'un chunk en mots, sur tout le corpus (utilisée par BM25)."""
    return int(np.mean([len(chunk['text'].split()) for chunk in iter_chunks(chunker)]))

def index_chunks(qdrant_client, collection_name, chunker, embedder, model_name, embedding_batch_size, sparse_embedder_options, per_language):    
    points = iter_points(chunker, embedder, model_name, embedding_batch_size, sparse_embedder_options, per_language)
    qdrant_client.upload_points(collection_name, points=points, batch_size=64)

def index_corpus():
    embedder_cfg = runner_settings['embedder']
    chunking_cfg = runner_settings['chunking']
    index_cfg = runner_settings['index']

    embedder = get_embedder()
    chunker = get_chunker(chunking_cfg['type'], embedder_cfg['model'], chunking_cfg['max_tokens'])
    qdrant_client = get_qdrant_client()

    collection_name = get_collection_name(
        embedder_name = embedder_cfg['model'],
        chunk_type = chunking_cfg['type'],
        chunk_size = chunking_cfg['max_tokens'],
        sparse_vector = index_cfg.get('sparse_vector'),
        context_line = chunking_cfg['context_line'],
        sparse_language = index_cfg.get('sparse_language'),
    )

    init_collection(qdrant_client, collection_name, embedder_cfg['vector_size'])

    convert_corpus()

    sparse_embedder_options = get_sparse_options(index_cfg)
    sparse_embedder_options['avg_len'] = probe_avg_len(chunker)
    per_language = index_cfg.get('sparse_language') == 'per_chunk'   # True avec exp03, False avec exp01/exp02

    index_chunks(
        qdrant_client, collection_name , chunker,
        embedder, embedder_cfg['model'], embedder_cfg['embedding_batch_size'], 
        sparse_embedder_options, per_language
        )

    print(f'{collection_name}: {qdrant_client.count(collection_name).count} points')   # 3. contrôle

if __name__ == '__main__':
    index_corpus()

