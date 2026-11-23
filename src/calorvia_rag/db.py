from calorvia_rag.config import settings
from psycopg.types.json import Jsonb
from psycopg.rows import dict_row
import psycopg as pg

def get_connection(autocommit = True):
    return pg.connect(settings.postgres_url, autocommit=autocommit)

def load_sql(name):
    return (settings.sql_statement_folder / f'{name}').read_text('utf-8')

def init_db():
    with get_connection() as conn:
        conn.execute(load_sql('schema.sql'))

def start_run(parameters):
    init_db()
    with get_connection() as conn:
        return conn.execute('INSERT INTO run(parameters) VALUES(%s) RETURNING run_id', (Jsonb(parameters),)).fetchone()[0]

def end_run(run_id, doc_processed, doc_ignored, doc_failed):
    with get_connection() as conn:
        conn.execute(
            'UPDATE run SET end_time = NOW(), doc_processed = %s, doc_ignored = %s, doc_failed = %s WHERE run_id = %s',
            (doc_processed, doc_ignored, doc_failed, run_id)
        )

def insert_log(run_id, log):
    with get_connection() as conn:
        conn.execute(
            '''INSERT INTO document (run_id, file_path, export_folder, file_name, file_format_, file_hash
                                    , status_, page_count, text_count, table_count, image_count, process_time, error)
            VALUES (%(run_id)s, %(file_path)s, %(export_folder)s, %(file_name)s, %(file_format_)s, %(file_hash)s,
                    %(status_)s, %(page_count)s, %(text_count)s, %(table_count)s, %(image_count)s, %(process_time)s, %(error)s)''',
            {'run_id': run_id, **log},
        )

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
    # section 2 : metadata
    'table_count', 'image_count', 'department', 'doc_type', 'doc_date', 'date_precision', 'period',
    'version', 'status', 'source_type', 'context_line',
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

def is_file_processed(file_path, file_hash):
    with get_connection() as conn:
        r = conn.execute(
            "SELECT 1 FROM document WHERE file_hash = (%s) AND status_ IN ('success', 'partial_success') LIMIT 1",
            (file_hash,)
        ).fetchone()
    return r is not None

def list_files_to_convert():
    """Fichiers du registre à convertir : indexés, et avec du texte (ni image ni scan)."""
    with get_connection() as conn:
        return conn.execute(
            '''SELECT path, sha256 FROM documents
               WHERE excluded_reason IS NULL
                 AND source_type NOT IN ('image', 'scan')
               ORDER BY path'''
        ).fetchall()

def list_documents_to_chunk():
    """Documents à découper, avec leurs métadonnées (mêmes filtres que list_files_to_convert)."""
    with get_connection() as conn:
        return conn.cursor(row_factory = dict_row).execute(
            '''SELECT path, sha256, format, department, doc_type, doc_date, period,
                      version, status, source_type, language, context_line
               FROM documents
               WHERE excluded_reason IS NULL
                 AND source_type NOT IN ('image', 'scan')
               ORDER BY path'''
        ).fetchall()

def get_experiment_split(experiment_id):
    """Le jeu de questions d'une expérience : 'test' pour la réserve, 'dev' sinon (les expériences d'avant le mode test n'ont pas de split)."""
    with get_connection() as conn:
        row = conn.execute("SELECT config->>'split' FROM experiments WHERE id = %s", (experiment_id,)).fetchone()
    if row is None:
        raise ValueError(f'Experiment {experiment_id} not found')
    return row[0] or 'dev'

def list_test_experiments():
    """Les expériences terminées sur la réserve de test : elle ne doit être évaluée qu'une fois."""
    with get_connection() as conn:
        return conn.execute(
            "SELECT id, name FROM experiments WHERE config->>'split' = 'test' AND status = 'done' ORDER BY id"
        ).fetchall()

def end_experiment(experiment_id, duration_s, status):
    with get_connection() as conn:
        conn.execute(
            'UPDATE experiments SET duration_s = %s, status = %s WHERE id = %s',
            (duration_s, status, experiment_id)
        )

def insert_answer(experiment_id, question_id, chunks, answer, latency_ms, llm_metrics):
    with get_connection() as conn:
        conn.execute(
            'INSERT INTO answers (experiment_id, question_id, chunks, answer, latency_ms, llm_metrics) VALUES (%s, %s, %s, %s, %s, %s)',
            (experiment_id, question_id, Jsonb(chunks), answer, latency_ms, Jsonb(llm_metrics))
        )

def get_answers(experiment_id):
    with get_connection() as conn:
        rows = conn.execute('SELECT question_id, answer, chunks FROM answers WHERE experiment_id = %s', (experiment_id,)).fetchall()
    return {question_id: (answer, chunks) for question_id, answer, chunks in rows}

def insert_scores(experiment_id, question_id, question_type, scores):
    with get_connection() as conn:
        conn.cursor().executemany(
            'INSERT INTO scores (experiment_id, question_id, question_type, metric, value, reason) VALUES (%s, %s, %s, %s, %s, %s)',
            [(experiment_id, question_id, question_type, metric, value, reason) for metric, value, reason in scores])

def list_documents_to_transcribe():
    """Images et PDF scannés à faire lire par le VLM (mêmes exclusions que le reste du corpus),
    avec les métadonnées de list_documents_to_chunk pour le payload de leurs chunks."""
    with get_connection() as conn:
        return conn.cursor(row_factory = dict_row).execute(
            '''SELECT path, sha256, format, department, doc_type, doc_date, period,
                      version, status, source_type, language, context_line
               FROM documents
               WHERE excluded_reason IS NULL AND source_type IN ('image', 'scan')
               ORDER BY path'''
        ).fetchall()

def list_scans_to_convert():
    """PDF scannés à lire par l'OCR de Docling (section 6, étape 2), pour les comparer au VLM."""
    with get_connection() as conn:
        return conn.execute(
            '''SELECT path, sha256 FROM documents
               WHERE excluded_reason IS NULL AND source_type = 'scan'
               ORDER BY path'''
        ).fetchall()

def list_scans_to_convert():
    """Documents numérisés à lire par l'OCR de Docling (section 6, étape 2), pour les comparer au VLM :
    les PDF scannés, et les photos de factures et de bons de livraison (les preuves des questions scan_ocr)."""
    with get_connection() as conn:
        return conn.execute(
            '''SELECT path, sha256 FROM documents
               WHERE excluded_reason IS NULL
                 AND (source_type = 'scan'
                      OR (source_type = 'image' AND doc_type IN ('facture', 'bon_de_livraison')))
               ORDER BY path'''
        ).fetchall()
