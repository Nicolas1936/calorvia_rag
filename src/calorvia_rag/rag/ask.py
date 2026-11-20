from calorvia_rag.config import settings, runner_settings
from calorvia_rag.qdrant import get_qdrant_client
from calorvia_rag.embedding import get_embedder
from calorvia_rag.rag.search import search_and_filter_chunks
from calorvia_rag.rag.rerank import rerank_chunks
from calorvia_rag.rag.translate import translate_question

from openai import AsyncOpenAI
from pathlib import Path

import asyncio

def get_llm_client():
    return AsyncOpenAI(
        base_url = settings.llm_url,
        api_key = settings.llm_server_api_key
    )

def build_prompt(query, chunks):
    prompt = ''
    for i, (chunk, score) in enumerate(chunks, start = 1):
        prompt += f'<passage id="{i}">\n{chunk.payload["text"]}\n</passage>\n'
    return prompt + f'\nQuestion: {query}'

async def get_response(query, chunks, llm_client):
    generation_cfg = runner_settings['generation']
    system_prompt = Path(generation_cfg['system_prompt']).read_text(encoding = 'utf-8')

    response = await llm_client.chat.completions.create(
        model = generation_cfg['model'],
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': build_prompt(query, chunks)},
        ],
        temperature = generation_cfg['temperature'],
        top_p = generation_cfg['top_p'],
        max_tokens = generation_cfg['max_tokens'],
        extra_body = {
            'top_k': generation_cfg['top_k'],
            'chat_template_kwargs': {'enable_thinking': generation_cfg['reasoning']},
        },
    )
    return response.choices[0].message.content, response.model_extra['timings']

async def generate_response(query, qdrant_client, embedder, llm_client):
    translations = None
    if runner_settings['search'].get('translate_query'):
        translations = await translate_question(query, llm_client)
    
    filtered_chunks = await asyncio.to_thread(search_and_filter_chunks, query, qdrant_client, embedder, None, translations)
    reranked_chunks = await asyncio.to_thread(rerank_chunks, query, filtered_chunks)
    response, llm_metrics = await get_response(query, reranked_chunks, llm_client)

    return response, llm_metrics, reranked_chunks

if __name__ == '__main__':
    response, llm_metrics, chunks = asyncio.run(generate_response(
        "Quelle vitesse est autorisée dans l'entrepôt de Gand ?",
        get_qdrant_client(), get_embedder(), get_llm_client()
    ))
    print(response)
    for i, (chunk, score) in enumerate(chunks, start = 1):
        print(f'[{i}]', round(score, 3), chunk.payload['document'], chunk.payload['chunk_index'])
