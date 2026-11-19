from calorvia_rag.config import settings, runner_settings

from deepeval.models import LocalModel
from deepeval.metrics import FaithfulnessMetric, GEval
from deepeval.test_case import LLMTestCase, SingleTurnParams
import random


def get_judge_model():
    return LocalModel(
        model = runner_settings['judge']['model'],
        base_url = settings.llm_url,
        api_key = settings.llm_server_api_key,
        temperature = 0,
        generation_kwargs = {'extra_body': {'chat_template_kwargs': {'enable_thinking': False}}}
    )

TRAP_STEPS = (
    "Identifier la valeur de la sortie attendue qui répond à la question.",
    "Identifier les valeurs erronées ou obsolètes présentes dans le contexte.",
    "Si la sortie réelle donne l'une des valeurs du contexte comme réponse, le score est 0.",
    "Si la sortie réelle donne la valeur de la sortie attendue, ou refuse de répondre, le score est 1. "
    "Si elle mentionne une valeur erronée seulement pour dire qu'elle a été corrigée ou remplacée, le score reste 1.",
)


def get_judge_metrics():
    judge_model = get_judge_model()
    return {
        'faithfulness': FaithfulnessMetric(model = judge_model, async_mode = False),
        'correctness': GEval(
            name = 'correctness',
            criteria = 'Determine whether the actual output is factually correct and complete compared to the expected output.',
            evaluation_params = [SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT, SingleTurnParams.EXPECTED_OUTPUT],
            model = judge_model, async_mode = False
        ),
        'trap_avoided': GEval(
            name = 'trap_avoided',
            criteria = TRAP_STEPS,
            evaluation_params = [SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT,
                                 SingleTurnParams.EXPECTED_OUTPUT, SingleTurnParams.CONTEXT],
            model = judge_model, async_mode = False
        )
    }

def get_judge_sample(questions):
    """N questions par type, tirées au hasard mais toujours les mêmes (graine fixe du .toml)."""
    judge_cfg = runner_settings['judge']
    rng = random.Random(judge_cfg['seed'])
    sample_ids = []
    for question_type in sorted({question['type'] for question in questions}):
        ids = [question['id'] for question in questions if question['type'] == question_type]
        sample_ids += rng.sample(ids, min(judge_cfg['samples_per_type'], len(ids)))
    return sample_ids

def judge_scores(question, answer, chunks, metrics):
    test_case = LLMTestCase(
        input = question['question'],
        actual_output = answer,
        expected_output = question['answer'],
        retrieval_context = [chunk['text'] for chunk in chunks],
        context = [snippet for trap in question['traps'] for snippet in trap['snippets']] or None,   # nouveau

    )

    scores = []
    for name, metric in metrics.items():
        try:
            metric.measure(test_case)
            scores.append((name, metric.score, metric.reason))
        except Exception as e:
            scores.append((name, None, f'{type(e).__name__}: {e}'))
    return scores
