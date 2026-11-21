## Relancer le projet
1. `git clone https://github.com/Nicolas1936/calorvia_rag.git`
2. Placer le corpus dans `data/calorvia/` et le jeu d'évaluation dans `data/calorvia_eval.json`
3. `cp .env.template .env` (renseigner les mots de passe), `uv sync`, `docker compose up -d`
4. Services : embedder (8001) et reranker (8002) dans vLLM ; Qwen, le juge Gemma et le VLM derrière llama-swap (8000), chargés à la demande
5. Ingestion puis expérience :
   - `uv run python -m calorvia_rag.etl.inventory`
   - `uv run python -m calorvia_rag.etl.vision` (images et scans lus une seule fois par le VLM, via llama-swap sur le port 8000 et non le port 8003 de l'énoncé ; cache dans `data/vision/`)
   - `uv run python -m calorvia_rag.etl.index` (conversion + chunks + Qdrant ; les transcriptions sont indexées si `include_images` / `include_scanned_pdfs` sont à `true` dans le TOML)
   - `uv run python -m calorvia_rag.evaluation.runner`
   - `uv run python -m calorvia_rag.evaluation.runner judge <id>`

Changer d'expérience : `RUNNER_CONFIG_PATH=experiments/<fichier>.toml` devant la commande.
