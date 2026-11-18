from calorvia_rag.config import settings, runner_settings

from deepeval.models import LocalModel
from deepeval.metrics import FaithfulnessMetric, GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams as SingleTurnParams
import random


def get_judge_model():
    return LocalModel(
        model = runner_settings['judge']['model'],
        base_url = settings.llm_url,
        api_key = settings.llm_server_api_key,
        temperature = 0,
        generation_kwargs = {'extra_body': {'chat_template_kwargs': {'enable_thinking': False}}}
    )

TRAP_CRITERIA = (
    'The context lists wrong or outdated values (a draft, an old version, a minute corrected later). '
    'Determine whether the actual output gives one of these values as the answer, instead of the expected output. '
    'Mentioning the wrong value only to say that it was corrected or replaced does not count.'
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
        'trap_answer': GEval(
            name = 'trap_answer',
            criteria = TRAP_CRITERIA,
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
