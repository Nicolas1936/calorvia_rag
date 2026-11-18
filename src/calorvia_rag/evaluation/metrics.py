from pathlib import Path
from ranx import Qrels, Run, evaluate
import re

REFUSAL = 'je ne dispose pas de cette information'

def normalize_numbers(text):
    """'4 568' -> '4568', '41,5' -> '41.5': the same rendering in chunks and evidence snippets."""
    text = re.sub(r'(?<=\d)[ \u00a0\u202f](?=\d{3}\b)', '', text)
    return re.sub(r'(?<=\d),(?=\d)', '.', text)

def normalize_path(path):
    """Sur le disque, certains noms de fichiers ont '_' à la place de l'apostrophe ; le jeu d'évaluation la garde."""
    return path.replace("'", '_').replace('’', '_')


def same_document(chunk, reference):
    """Le chunk vient-il du document cité par la preuve (ou par le piège) ?"""
    return normalize_path(chunk['document']) == normalize_path(reference['document'])

def normalize(text):
    """Même rendu des nombres et des espaces, des deux côtés de la comparaison."""
    text = normalize_numbers(text)
    return re.sub(r'\s+', ' ', text).strip()

def judge_chunk(chunk, evidence):
    """True si le chunk vient du document de la preuve et contient tous ses extraits."""
    return same_document(chunk, evidence) and all(
        normalize(snippet) in normalize(chunk['text']) for snippet in evidence['snippets']
    )

def trap_hit(chunks, question):
    """True if a retrieved chunk contains a wrong or outdated answer listed in `traps`."""
    return any(
        same_document(chunk, trap)
        and all(normalize(snippet) in normalize(chunk['text']) for snippet in trap['snippets'])
        for chunk in chunks for trap in question['traps']
    )

def get_evidence_id(evidence, i):
    if evidence['fact'] is None:
        return f'extra_{i}'
    return f"fact_{evidence['fact']}"

def build_qrels(question):
    return {get_evidence_id(evidence, i): evidence['grade'] for i, evidence in enumerate(question['evidence'])}

def build_run(question, chunks):
    run = {}
    for rank, chunk in enumerate(chunks):
        score = float(len(chunks) - rank)
        evidence_ids = [get_evidence_id(evidence, i) for i, evidence in enumerate(question['evidence']) if judge_chunk(chunk, evidence)]
        for evidence_id in evidence_ids or [f'chunk_{rank}']:
            run.setdefault(evidence_id, score)
    return run

def retrieval_scores(question, chunks, k):
    metrics = {
        f'hit@{k}': f'hit_rate@{k}-l2',
        'mrr': 'mrr-l2',
        f'recall@{k}': f'recall@{k}-l2',
        f'ndcg@{k}': f'ndcg@{k}',
    }
    qrels = Qrels({question['id']: build_qrels(question)})
    run = Run({question['id']: build_run(question, chunks)})
    values = evaluate(qrels, run, list(metrics.values()))
    return [(name, float(values[ranx_name]), None) for name, ranx_name in metrics.items()]

def is_refusal(answer):
    return REFUSAL in answer.lower()
