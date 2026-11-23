# Calorvia RAG

Un assistant de questions-réponses sur le corpus documentaire de Calorvia : PDF, Word, Excel, PowerPoint, HTML, images et scans, en français, en néerlandais et en anglais. Les réponses sont en français, avec la citation des passages utilisés.

Le projet suit l'énoncé du laboratoire (`laboratoire_calorvia_enonce.md`). La démarche, le tableau comparatif des expériences et leur analyse sont dans [RAPPORT.md](RAPPORT.md).

## Résultats de `v1.0`

| | Jeu de développement (127 questions) | Réserve de test (31 questions, évaluée une fois) |
|---|---|---|
| Preuve dans les 5 / les 10 premiers passages (hit@5 / hit@10) | 0,943 / 0,951 | 0,800 / 0,933 |
| Réponse juste et complète selon le juge (correctness, 31 questions) | 0,82 | 0,77 |
| Réponses qui reprennent une valeur périmée ou non officielle | 0/17 | 0/4 |
| Temps de réponse moyen | 9,5 s | 9,5 s |

## Le pipeline

1. **Inventaire** (`etl/inventory.py`, `etl/metadata.py`). Le registre des documents est enregistré dans PostgreSQL : format, langue, doublons, et les métadonnées tirées du chemin et du contenu (type, date, version, statut).
2. **Lecture.**
   - **Docling** (`etl/convert.py`) lit les PDF texte, les fichiers Word, PowerPoint, HTML, Markdown et CSV.
   - **openpyxl** (`etl/excel.py`) lit les classeurs Excel, avec une phrase par ligne de tableau.
   - **Le VLM** Qwen3.8-27B (`etl/vision.py`) transcrit les images, les scans et les graphiques insérés dans les PDF. Les transcriptions sont mises en cache dans `data/vision/`.
3. **Chunks** (`etl/chunker.py`). Le HybridChunker de Docling découpe en chunks de 512 tokens au plus, mesurés avec le tokenizer de bge-m3. Chaque chunk commence par une ligne de contexte (titre et dossier du document).
4. **Index** (`etl/index.py`). Une collection Qdrant contient deux vecteurs par chunk : un vecteur dense bge-m3, et un vecteur BM25 avec le stemmer de la langue du chunk. Le payload reprend les métadonnées du registre.
5. **Réponse** (`rag/`).
   - Une recherche hybride fusionne les deux listes par RRF et retient 30 candidats. Un filtre `must_not` écarte les documents au statut `projet`.
   - Le reranker bge-reranker-v2-m3 garde 10 passages.
   - Qwen3.8-27B génère la réponse avec `prompts/detailed_fr_versions.txt`. Les passages lui sont présentés du plus ancien au plus récent, chacun avec sa date.
6. **Évaluation** (`evaluation/`).
   - Les métriques de recherche sont calculées avec ranx : hit, MRR, recall, nDCG.
   - Le runner compte aussi les refus et les passages pièges.
   - Le juge Gemma 4 26B note les réponses avec deepeval : correctness, faithfulness et `trap_avoided`.

## Prérequis

- **Un GPU NVIDIA de 24 Go.** L'embedder et le reranker restent chargés. llama-swap charge à la demande un seul LLM à la fois : le générateur, le juge ou le VLM.
- **Docker** avec le NVIDIA Container Toolkit, **[uv](https://docs.astral.sh/uv/)** et Python 3.12.
- **Le corpus et le jeu d'évaluation** fournis avec l'énoncé, qui ne sont pas dans le dépôt. Le corpus va dans `data/calorvia/`, le jeu d'évaluation dans `data/calorvia_eval.json`.

### Les modèles

Tous les modèles sont rangés sous un même dossier racine, `MODELS_DIR`, monté en `/models` dans les conteneurs. L'application lit les modèles Docling et le tokenizer de bge-m3 dans `MODELS_FOLDER = $MODELS_DIR/rag`.

| Modèle | Rôle | Emplacement sous `MODELS_DIR` | Téléchargement |
|---|---|---|---|
| bge-m3 | embedder (vLLM), et tokenizer du chunker | `rag/embedder/bge-m3/` | `uv run hf download BAAI/bge-m3 --local-dir $MODELS_DIR/rag/embedder/bge-m3` |
| bge-reranker-v2-m3 | reranker (vLLM) | `rag/reranker/bge-reranker-v2-m3/` | `uv run hf download BAAI/bge-reranker-v2-m3 --local-dir $MODELS_DIR/rag/reranker/bge-reranker-v2-m3` |
| Modèles Docling | mise en page, tableaux, OCR | `rag/docling/` | `uv run docling-tools models download -o $MODELS_DIR/rag/docling` |
| Qwen3.8-27B (GGUF Q4_K_XL) et son mmproj | génération, et VLM pour l'ETL | `qwen3.8-27b/llama/Qwen3.8-27B-UD-Q4_K_XL.gguf`, `qwen3.8-27b/llama/mmproj-F16.gguf` | dépôt Hugging Face à compléter |
| Gemma 4 26B A4B (GGUF Q4_K_XL) et son draft MTP | juge | `gemma4-26b-a4b/llama/gemma-4-26B-A4B-it-UD-Q4_K_XL.gguf`, `gemma4-26b-a4b/llama/mtp-gemma-4-26B-A4B-it.gguf` | dépôt Hugging Face à compléter |

## Installation

```bash
git clone https://github.com/Nicolas1936/calorvia_rag.git
cd calorvia_rag
# Copier le corpus dans data/calorvia/ et le jeu d'évaluation dans data/calorvia_eval.json
cp .env.template .env                        # puis renseigner les valeurs, dont MODELS_DIR et MODELS_FOLDER
uv sync
docker compose up -d                         # PostgreSQL, Qdrant, embedder, reranker, llama-swap
docker compose --profile on-demand create    # conteneurs des LLM, démarrés par llama-swap à la demande
```

| Port | Service |
|---|---|
| 5432 | PostgreSQL : registre des documents, journal de conversion, expériences, réponses et scores |
| 6333 | Qdrant (tableau de bord : http://localhost:6333/dashboard) |
| 8000 | llama-swap : `qwen3.8-27b` (génération), `gemma-4-26b` (juge), `qwen3.8-vision` (VLM). Configuration dans `config.yaml` |
| 8001 | embedder `bge-m3` (vLLM) |
| 8002 | reranker `bge-reranker-v2-m3` (vLLM) |

## Reproduire `v1.0`

```bash
uv run python -m calorvia_rag.etl.inventory              # registre des documents et métadonnées
uv run python -m calorvia_rag.etl.vision                 # images, scans et graphiques lus par le VLM (≈ 8,5 min la première fois)
curl -s http://localhost:8000/unload                     # décharge le VLM : la conversion Docling a besoin du GPU
uv run python -m calorvia_rag.etl.index                  # conversion Docling, chunks et collection Qdrant de la configuration
uv run python -m calorvia_rag.evaluation.runner          # les 127 questions du jeu de développement
uv run python -m calorvia_rag.evaluation.runner judge <id>
uv run python -m calorvia_rag.evaluation.export          # results/experiments.csv et results/scores_by_type.csv
```

- **Les tables PostgreSQL** sont créées au premier lancement (`sql_queries/schema.sql`).
- **La conversion Docling utilise le GPU.**
  - Après `etl.vision`, le VLM reste chargé : llama-swap ne décharge pas un modèle de lui-même. Il ne laisse alors pas assez de mémoire au modèle de mise en page de Docling, et des PDF échouent faute de mémoire. `curl -s http://localhost:8000/unload` libère le GPU, et llama-swap rechargera le générateur à la demande pour le runner.
  - Si le GPU reste trop occupé, par exemple par le bureau, mets `OCR_DEVICE=cpu` dans `.env`. La conversion est plus lente, mais elle n'utilise plus le GPU.
- **En cas d'échec de conversion**, `etl.index` s'arrête avant de toucher la collection Qdrant et liste les documents concernés. Une nouvelle exécution ne reconvertit que ceux-là.
- **La conversion et les transcriptions sont mises en cache.** Les exports Docling vont dans `data/calorvia_export/`, les transcriptions dans `data/vision/`. Une nouvelle exécution ne traite que les fichiers nouveaux, modifiés ou en échec.
- **Le runner refuse de démarrer** si la collection de la configuration est absente ou vide.
- **La réserve de test** se lance avec `uv run python -m calorvia_rag.evaluation.runner test`, **une seule fois**, sur la configuration finale.
  - Le mode `test` refuse de démarrer si le code n'est pas commité, ou si la réserve a déjà été évaluée.
  - Le juge note alors les 31 questions, au lieu de 2 par type.
- **Pour poser une question** : `uv run python -m calorvia_rag.rag.ask`.
- **Reproductibilité** : un clone propre tiré de GitHub, avec sa propre base et son propre Qdrant, reproduit les métriques de recherche de `v1.0` à 0,001 près, sans reprendre aucun piège. Le test et les cinq problèmes qu'il a permis de corriger sont décrits à la fin de [RAPPORT.md](RAPPORT.md).

## Configuration

- **Une expérience est un fichier TOML** dans `experiments/`. La configuration par défaut, celle de `v1.0`, est `exp14_passages_by_date.toml`. Pour en utiliser une autre, place `RUNNER_CONFIG_PATH=experiments/<fichier>.toml` devant chaque commande (index, runner, juge).
- **Le nom de la collection Qdrant dépend du TOML** : embedder, chunking, ligne de contexte, BM25, lecteur Excel, images et scans. Si tu changes un de ces réglages, relance `etl.index` avec le même `RUNNER_CONFIG_PATH`. Les réglages de la recherche, du reranking et de la génération ne demandent pas de réindexation.
- **Chaque expérience est enregistrée** avec son commit et `git_dirty`. Les expériences citées dans le rapport ont toutes tourné sur du code commité.
- **Le fichier `.env`** est décrit dans `.env.template`. Pour changer l'adresse de Qdrant ou du serveur de LLM, renseigne l'URL complète (`QDRANT_URL`, `LLM_URL`). `QDRANT_PORT` ou `IP_ADDRESS` seuls ne modifient pas les URL.

## Structure du dépôt

```
src/calorvia_rag/
  config.py, db.py, qdrant.py, embedding.py, git_info.py
  etl/          inventory, metadata, convert, excel, vision, chunker, index
  rag/          search, rerank, translate, ask
  evaluation/   runner, metrics, judge, export
experiments/    un TOML par expérience (exp01 à exp14)
prompts/        prompts système
sql_queries/    schéma PostgreSQL et diagramme entité-relation
results/        résultats exportés de PostgreSQL (CSV)
notebooks/      exploration du corpus et des pistes
RAPPORT.md      démarche, tableau comparatif et analyse des expériences
docker-compose.yml, config.yaml (llama-swap), .env.template
```

## Versions

Chaque section du laboratoire a sa branche, fusionnée dans `main` puis taguée :

| Tag | Contenu |
|---|---|
| `v0.1-inventaire` | inventaire et métadonnées (sections 1 et 2) |
| `v0.2-baseline` | version de référence : documents texte, ligne de contexte (section 3) |
| `v0.3-langues` | stemmer BM25 par langue, prompt « réponds en français » (section 4) |
| `v0.4-excel` | classeurs lus par openpyxl (section 5) |
| `v0.5-images` | images, scans et graphiques transcrits par le VLM (section 6) |
| `v0.6-versions` | filtre sur le statut, consignes sur les versions, 10 passages triés par date (section 7) |
| `v1.0` | évaluation finale sur la réserve de test (section 8) |
