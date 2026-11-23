from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

import tomllib

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')


    postgres_url: str

    qdrant_api_key: str | None
    qdrant_port: int = 6333
    qdrant_ip_address: str = '127.0.0.1'
    qdrant_url: str = f'http://{qdrant_ip_address}:{qdrant_port}'

    # LLM server provider
    llm_server_api_key: str
    ip_address: str = '127.0.0.1'
    llm_url: str = f'http://{ip_address}:8000/v1'
    embedding_url: str = f'http://{ip_address}:8001/v1'
    rerank_url: str = f'http://{ip_address}:8002/rerank'
    llm_parallel_requests: int = 3

    # folder paths
    corpus_folder: Path = Path('./data/calorvia')
    processed_documents_folder: Path = Path('./data/calorvia_export')
    sql_statement_folder: Path = Path('./sql_queries')
    eval_dataset_path: Path = Path('./data/calorvia_eval.json')
    models_folder: Path

    # Converter Settings
    ocr_device: str = 'cuda'
    ocr_num_threads: int = 6

    vision_model: str = 'qwen3.8-vision'      # VLM servi par llama-swap (port 8000), pas sur le port 8003 de l'énoncé
    vision_folder: Path = Path('./data/vision')



    # Language support
    corpus_language: str = 'french'

    # Run Config
    runner_config_path: Path = Path('./experiments/exp10_pdf_charts.toml')

def load_runner_settings(config_path):
    with open(config_path, 'rb') as f:
        return tomllib.load(f)

settings = Settings()
runner_settings = load_runner_settings(settings.runner_config_path)
