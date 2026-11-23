"""Exporte les résultats de PostgreSQL dans results/*.csv, pour les versionner avec le code :
une ligne par expérience, et la moyenne de chaque métrique par expérience et par type de question.
Usage : uv run python -m calorvia_rag.evaluation.export [dossier]   (par défaut : results/)"""
from calorvia_rag.db import get_connection

from pathlib import Path

import sys

QUERIES = {
    'experiments': '''
        SELECT id, name, status, git_commit, git_dirty, round(duration_s) AS duration_s, started_at
        FROM experiments ORDER BY id''',
    'scores_by_type': '''
        SELECT experiment_id, question_type, metric, count(value) AS n, round(avg(value)::numeric, 3) AS mean
        FROM scores
        GROUP BY experiment_id, question_type, metric
        ORDER BY experiment_id, question_type, metric''',
}

def export_results(folder = Path('./results')):
    folder.mkdir(parents = True, exist_ok = True)
    with get_connection() as conn, conn.cursor() as cursor:
        for name, query in QUERIES.items():
            path = folder / f'{name}.csv'
            with open(path, 'wb') as f, cursor.copy(f'COPY ({query}) TO STDOUT WITH (FORMAT CSV, HEADER)') as copy:
                for data in copy:
                    f.write(data)
            print(path)


if __name__ == '__main__':
    export_results(Path(sys.argv[1]) if len(sys.argv) > 1 else Path('./results'))
