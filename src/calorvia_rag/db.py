from calorvia_rag.config import settings
from psycopg.types.json import Jsonb
import psycopg as pg

def get_connection(autocommit = True):
    return pg.connect(settings.postgres_url, autocommit=autocommit)

def load_sql(name):
    return (settings.sql_statement_folder / f'{name}').read_text('utf-8')

def init_db():
    with get_connection() as conn:
        conn.execute(load_sql('schema.sql'))

def start_experiment(name, config, git_commit, git_dirty):
    init_db()
    with get_connection() as conn:
        return conn.execute(
            'INSERT INTO experiments(name, config, git_commit, git_dirty) VALUES(%s, %s, %s, %s) RETURNING id',
            (name, Jsonb(config), git_commit, git_dirty)
        ).fetchone()[0]