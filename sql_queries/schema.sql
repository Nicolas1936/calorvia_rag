CREATE TABLE IF NOT EXISTS run(
    run_id SERIAL CONSTRAINT PK_RUN_ID PRIMARY KEY,
    start_time TIMESTAMPTZ DEFAULT NOW(),
    end_time TIMESTAMPTZ,
    doc_processed INT,
    doc_ignored INT,
    doc_failed INT,
    parameters JSONB
);

CREATE TABLE IF NOT EXISTS document (
    document_id SERIAL CONSTRAINT PK_DOCUMENT_ID PRIMARY KEY,
    run_id INT CONSTRAINT FK_DOCUMENT_RUN REFERENCES run(run_id),
    file_path TEXT,
    export_folder TEXT,
    file_name TEXT,
    file_format_ TEXT,
    file_hash TEXT,
    status_ TEXT,
    page_count INT,
    text_count INT,
    table_count INT,
    image_count INT,
    process_time FLOAT,
    error TEXT
);

CREATE TABLE IF NOT EXISTS experiments (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    config JSONB NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    duration_s REAL,
    status TEXT NOT NULL DEFAULT 'running'
);

ALTER TABLE experiments
    ADD COLUMN IF NOT EXISTS git_commit TEXT,
    ADD COLUMN IF NOT EXISTS git_dirty BOOLEAN;

CREATE TABLE IF NOT EXISTS answers (
    experiment_id INT NOT NULL REFERENCES experiments(id),
    question_id TEXT NOT NULL,
    chunks JSONB NOT NULL,
    answer TEXT,
    latency_ms REAL,
    llm_metrics JSONB,
    PRIMARY KEY (experiment_id, question_id)
);

CREATE TABLE IF NOT EXISTS scores (
    experiment_id INT NOT NULL REFERENCES experiments(id),
    question_id TEXT NOT NULL,
    question_type TEXT NOT NULL,
    metric TEXT NOT NULL,
    value REAL,
    reason TEXT,
    PRIMARY KEY (experiment_id, question_id, metric)
);

CREATE TABLE IF NOT EXISTS documents (
    path TEXT PRIMARY KEY,              -- relative to the corpus root, as in the evaluation set
    file_name TEXT NOT NULL,
    format TEXT NOT NULL,
    size_bytes BIGINT NOT NULL,
    sha256 TEXT NOT NULL,               -- of the bytes: exact copies
    content_sha256 TEXT,                -- of the text: copies saved separately (other bytes, same text)
    page_count INT,                     -- PDF pages, PPTX slides, XLSX sheets, 1 for images; NULL for DOCX, HTML, MD, CSV
    has_text_layer BOOLEAN,             -- PDF only: FALSE means a scan, to be read with OCR or the VLM
    pdf_kind TEXT,                      -- PDF only: 'scan', 'texte + images' (charts to read with the VLM) or 'texte'
    words INT,                          -- words in the raw text (0 for images and scans)
    language TEXT,                      -- fr, nl, en, de; NULL for images, scans and files without text
    read_error TEXT,
    excluded_reason TEXT,               -- NULL = indexed
    duplicate_of TEXT,                  -- for duplicates: the copy that is kept
    inventoried_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS documents_sha256 ON documents (sha256);
CREATE INDEX IF NOT EXISTS documents_content_sha256 ON documents (content_sha256);
