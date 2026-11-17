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


INVENTORY_COLUMNS = (
    'path', 'file_name', 'format', 'size_bytes', 'sha256', 'content_sha256', 'page_count', 'has_text_layer',
    'pdf_kind', 'words', 'language', 'read_error', 'excluded_reason', 'duplicate_of',
)

def save_inventory(rows):
    """Replace the registry with the current state of the corpus, in one transaction."""
    init_db()
    columns = ', '.join(INVENTORY_COLUMNS)
    placeholders = ', '.join(f'%({column})s' for column in INVENTORY_COLUMNS)
    updates = ', '.join(f'{column} = EXCLUDED.{column}' for column in INVENTORY_COLUMNS if column != 'path')
    with get_connection(autocommit = False) as conn:
        conn.cursor().executemany(
            f'''INSERT INTO documents ({columns}) VALUES ({placeholders})
                ON CONFLICT (path) DO UPDATE SET {updates}, inventoried_at = NOW()''',
            rows,
        )
        conn.execute('DELETE FROM documents WHERE NOT (path = ANY(%s))', ([row['path'] for row in rows],))
