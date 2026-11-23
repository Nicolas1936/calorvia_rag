from calorvia_rag.config import settings, runner_settings
from calorvia_rag.db import (start_experiment, end_experiment, insert_answer, insert_scores, get_answers,
                             get_experiment_split, list_test_experiments)
from calorvia_rag.qdrant import get_qdrant_client, get_current_collection_name
from calorvia_rag.embedding import get_embedder
from calorvia_rag.rag.ask import generate_response, get_llm_client
from calorvia_rag.evaluation.metrics import retrieval_scores, is_refusal, trap_hit
from calorvia_rag.evaluation.judge import get_judge_metrics, get_judge_sample, judge_scores
from calorvia_rag.git_info import git_state

from openai import OpenAI
from pathlib import Path
from time import perf_counter

import asyncio
import json
import sys

def is_test_question(question):
    """Réserve de test : les questions dont le numéro est un multiple de 5 (Q005, Q010… Q155)."""
    return int(question['id'][1:]) % 5 == 0

def load_questions(path, split = 'dev'):
    """Le jeu de développement (127 questions, split = 'dev') ou la réserve de test (31 questions, split = 'test')."""
    with open(path, encoding = 'utf-8') as f:
        return [question for question in json.load(f) if is_test_question(question) == (split == 'test')]

def get_experiment_config(split = 'dev'):
    generation_cfg = runner_settings['generation']
    system_prompt = Path(generation_cfg['system_prompt']).read_text(encoding = 'utf-8')
    return {**runner_settings, 'split': split, 'generation': {**generation_cfg, 'system_prompt_text': system_prompt}}

def check_collection():
    """Le runner ne démarre pas sur une collection absente ou vide : l'expérience ne serait qu'une suite de refus."""
    qdrant_client = get_qdrant_client()
    collection_name = get_current_collection_name()
    if not qdrant_client.collection_exists(collection_name) or qdrant_client.count(collection_name).count == 0:
        sys.exit(f'Collection Qdrant {collection_name} absente ou vide : lance d\'abord '
                 'uv run python -m calorvia_rag.etl.index, avec le même RUNNER_CONFIG_PATH.')

def check_test_run(git_dirty):
    """La réserve de test ne s'évalue qu'une fois, sur du code commité : sinon, le run s'arrête avant de commencer."""
    if git_dirty:
        sys.exit('Mode test refusé : modifications non commitées (git_dirty = true).')
    done = list_test_experiments()
    if done:
        experiment_id, name = done[0]
        sys.exit(f'Mode test refusé : la réserve a déjà été évaluée (expérience {experiment_id}, {name}).')

def evaluate_question(question, answer, chunks):
    k = runner_settings['reranker']['top_k']
    scores = [('refusal', float(is_refusal(answer)), None)]
    if question['evidence']:
        scores += retrieval_scores(question, chunks, k)
    if question['traps']:
        scores.append(('trap_hit', float(trap_hit(chunks, question)), None))
    return scores

async def answer_question(experiment_id, question, qdrant_client, embedder, llm_client, semaphore):
    async with semaphore:
        begin = perf_counter()
        answer, llm_metrics, reranked_chunks = await generate_response(question['question'], qdrant_client, embedder, llm_client)
        latency_ms = (perf_counter() - begin) * 1000

    chunks = [{**chunk.payload, 'score': score} for chunk, score in reranked_chunks]
    insert_answer(experiment_id, question['id'], chunks, answer, latency_ms, llm_metrics)
    insert_scores(experiment_id, question['id'], question['type'], evaluate_question(question, answer, chunks))
    print(question['id'], question['type'], f'{latency_ms:.0f} ms')

async def answer_questions(experiment_id, questions):
    qdrant_client = get_qdrant_client()
    embedder = get_embedder()
    llm_client = get_llm_client()
    semaphore = asyncio.Semaphore(settings.llm_parallel_requests)

    await asyncio.gather(*[
        answer_question(experiment_id, question, qdrant_client, embedder, llm_client, semaphore)
        for question in questions
    ])

def run_experiment(split = 'dev'):
    questions = load_questions(settings.eval_dataset_path, split)
    check_collection()

    git_commit, git_dirty = git_state()
    if split == 'test':
        check_test_run(git_dirty)
    elif git_dirty:
        print('⚠️  Modifications non commitées : le commit enregistré ne reproduit pas exactement cette expérience.')

    name = runner_settings['name'] if split == 'dev' else f"{runner_settings['name']}_test"
    experiment_id = start_experiment(name, get_experiment_config(split), git_commit, git_dirty)
    print('Experiment', experiment_id, f'({name}, {len(questions)} questions)')
    start = perf_counter()
    status = 'failed'

    try:
        asyncio.run(answer_questions(experiment_id, questions))
        status = 'done'
    finally:
        end_experiment(experiment_id, perf_counter() - start, status)

def get_served_models():
    llm_client = OpenAI(base_url = settings.llm_url, api_key = settings.llm_server_api_key)
    return [model.id for model in llm_client.models.list()]

def judge_experiment(experiment_id):
    judge_model = runner_settings['judge']['model']
    if judge_model not in get_served_models():
        raise ValueError(f'The judge model {judge_model} is not served by the LLM server')

    split = get_experiment_split(experiment_id)
    questions = load_questions(settings.eval_dataset_path, split)
    answers = get_answers(experiment_id)
    judge_metrics = get_judge_metrics()
    # Réserve de test : ses 31 questions sont toutes jugées. Jeu de développement : l'échantillon de N questions par type.
    judge_sample = [question['id'] for question in questions] if split == 'test' else get_judge_sample(questions)

    for question in questions:
        names = []
        if question['id'] in judge_sample:
            names += ['faithfulness', 'correctness']
        if question['traps']:
            names.append('trap_avoided')
        if not names:
            continue

        answer, chunks = answers[question['id']]
        metrics = {name: judge_metrics[name] for name in names}
        insert_scores(experiment_id, question['id'], question['type'], judge_scores(question, answer, chunks, metrics))
        print(question['id'], question['type'], ', '.join(names))



if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'judge':
        for experiment_id in sys.argv[2:]:
            judge_experiment(int(experiment_id))
    elif len(sys.argv) > 1 and sys.argv[1] == 'test':
        run_experiment('test')                  # la réserve de test : une seule fois, avec la configuration finale
    else:
        run_experiment()
