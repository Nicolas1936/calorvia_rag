from calorvia_rag.config import settings, runner_settings
from calorvia_rag.qdrant import get_qdrant_client
from calorvia_rag.embedding import get_embedder
from calorvia_rag.rag.search import search_and_filter_chunks
from calorvia_rag.rag.rerank import rerank_chunks
from calorvia_rag.rag.translate import translate_question

from openai import AsyncOpenAI
from pathlib import Path
from time import perf_counter

import asyncio
import re
import sys

def get_llm_client():
    return AsyncOpenAI(
        base_url = settings.llm_url,
        api_key = settings.llm_server_api_key
    )

def ordered_passages(chunks):
    """Les passages numérotés par rang du reranker, dans l'ordre où le prompt les présente.
    Avec `passage_order = 'date'` (TOML) : les passages sans date d'abord, puis du plus ancien au plus récent ;
    à date égale, l'ordre du reranker. Le numéro reste le rang : une citation [n] renvoie au n-ième chunk enregistré."""
    numbered = list(enumerate(chunks, start = 1))
    if runner_settings['generation'].get('passage_order') != 'date':
        return numbered
    return sorted(numbered, key = lambda item: item[1][0].payload.get('doc_date') or '')

def build_prompt(query, chunks):
    by_date = runner_settings['generation'].get('passage_order') == 'date'
    prompt = ''
    for i, (chunk, score) in ordered_passages(chunks):
        date = chunk.payload.get('doc_date')
        attributes = f' date="{date}"' if by_date and date else ''
        prompt += f'<passage id="{i}"{attributes}>\n{chunk.payload["text"]}\n</passage>\n'
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
    reranked_chunks = await asyncio.to_thread(rerank_chunks, query, filtered_chunks, translations)
    response, llm_metrics = await get_response(query, reranked_chunks, llm_client)

    return response, llm_metrics, reranked_chunks

def cited_passages(answer, chunks):
    """Les passages cités par la réponse ([n], le rang au reranking), par numéro croissant."""
    numbers = sorted({int(n) for n in re.findall(r'\[(\d+)\]', answer) if 1 <= int(n) <= len(chunks)})
    return [(n, chunks[n - 1][0].payload) for n in numbers]

def format_source(n, payload):
    """Une ligne par source : document, page d'un scan, date. Pour une image, son adresse cliquable dans le terminal."""
    line = ' · '.join([f'[{n}] {payload["document"]}']
                      + ([f'page {payload["page"] + 1}'] if payload.get('page') is not None else [])
                      + ([payload['doc_date']] if payload.get('doc_date') else []))
    if payload.get('image_path'):
        line += '\n      ' + (settings.corpus_folder / payload['image_path']).resolve().as_uri()
    return line

async def ask(question, qdrant_client, embedder):
    async with get_llm_client() as llm_client:      # un client par question : chaque asyncio.run a sa boucle d'événements
        begin = perf_counter()
        answer, _, chunks = await generate_response(question, qdrant_client, embedder, llm_client)
        return answer, chunks, perf_counter() - begin

def show(question, qdrant_client, embedder):
    answer, chunks, seconds = asyncio.run(ask(question, qdrant_client, embedder))
    print(f'\n{answer}\n')
    sources = cited_passages(answer, chunks)
    if sources:
        print('Sources :')
        for n, payload in sources:
            print('  ' + format_source(n, payload))
    print(f'\n({seconds:.1f} s, {len(chunks)} passages lus)')

def main():
    """Une question en argument, ou une suite de questions au clavier (ligne vide pour quitter)."""
    qdrant_client, embedder = get_qdrant_client(), get_embedder()
    print(f"Configuration : {runner_settings['name']}")
    if len(sys.argv) > 1:
        show(' '.join(sys.argv[1:]), qdrant_client, embedder)
        return
    print('Posez vos questions (ligne vide pour quitter).')
    while True:
        try:
            question = input('\nQuestion : ').strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not question:
            break
        show(question, qdrant_client, embedder)


if __name__ == '__main__':
    main()
