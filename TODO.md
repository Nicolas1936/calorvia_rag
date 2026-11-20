# Étapes restantes du projet

_État au 20 novembre 2026, branche `feat/langues`._

Tu as fini les sections 0 à 3 : l'inventaire, les métadonnées, la version de référence avec la ligne de contexte, les tags `v0.1` et `v0.2` poussés, l'export CSV et la section 3 du rapport. Tu es sur `feat/langues`, mais cette branche ne contient que le commit du rapport : rien de la section 4 n'est encore codé. Il te reste les sections 4 à 8, la fin du rapport, le README et la démo.

## 0. À corriger tout de suite

1. **Ton dépôt GitHub est public.** L'énoncé le veut privé, avec le formateur invité comme collaborateur (Settings → Change visibility, puis Collaborators). Le nom attendu est `rag-calorvia` et le tien est `calorvia_rag`. Demande au formateur si ça compte. Si tu renommes, change l'adresse avec `git remote set-url` et l'URL dans le README.
2. La seule modification en cours dans le notebook est le nom du kernel. Annule-la avec `git restore notebooks/labo_calorvia_pistes.ipynb` : sinon ta prochaine expérience sera enregistrée avec `git_dirty = true`.

## 1. Section 4 : les langues (`feat/langues` → `v0.3-langues`)

Fais une expérience par changement :
1. **Stemmer selon la langue** : aujourd'hui, [embedding.py:13-17](src/calorvia_rag/embedding.py#L13-L17) applique le stemmer `french` à tous les chunks. À l'indexation, passe la langue du chunk (`fr`→`french`, `nl`→`dutch`, `en`→`english`). Elle est déjà dans le payload ([chunker.py:42](src/calorvia_rag/etl/chunker.py#L42)). Ajoute ce réglage au nom de la collection pour garder l'index de la baseline.
2. **Traduction de la question** en néerlandais et en anglais par le LLM : trois recherches hybrides, chacune avec son stemmer, fusionnées par RRF, puis le reranker (notebook, 1.3). Active-la par une option dans le TOML.
3. **Prompt** : ajoute « réponds en français même si le passage est en néerlandais ou en anglais », dans un nouveau fichier de `prompts/`. Ce changement touche la génération, donc lance aussi le juge.

À mesurer : `multilingual`, tous les autres types et le temps de réponse (la traduction ajoute un appel au LLM).

## 2. Section 5 : les fichiers Excel (`feat/excel` → `v0.4-excel`)

1. Crée `etl/excel.py` (notebook, partie 2) :
   - `openpyxl` avec `data_only=True`, un passage par onglet ;
   - retrouver les tableaux : titre, en-tête, lignes, notes ;
   - afficher les valeurs comme dans Excel (pourcentages, dates) ;
   - une phrase par ligne, avec le fichier, l'onglet, le titre du tableau et la période ;
   - pour les grands tableaux, des paquets de lignes avec l'en-tête répété, plus un chunk de résumé ;
   - dans le payload : fichier, onglet, numéro de ligne, période, version.
2. Fais lire les `.xlsx` par ce module au lieu de Docling, puis lance une expérience.
3. Pour `excel_reasoning`, compare deux approches : le RAG seul, et des fonctions de calcul (polars ou SQL) que le LLM choisit. Ça fait une deuxième expérience.

À mesurer : `excel_lookup`, `excel_reasoning`, et les pièges du budget et du tarif (`version_trap`). `normalize_numbers` est déjà en place, rien à faire de ce côté.

## 3. Section 6 : les images et les scans (`feat/vlm` → `v0.5-images`)

1. Crée `etl/vision.py` : il transcrit **une seule fois** les 54 images et toutes les pages des 9 PDF scannés. Garde les transcriptions dans un cache sur disque, avec l'empreinte SHA-256 comme clé, et enregistre le temps de chaque transcription.
   - Le service `llama-vision` est déjà dans `docker-compose.yml`. Avec 24 Go de VRAM, llama-swap devrait décharger Qwen pendant cette étape.
   - Écris dans le README que le VLM passe par llama-swap sur le port 8000, et non sur le port 8003 de l'énoncé.
2. Lis les graphiques des deux PDF (l'annexe sur le télétravail et le rapport RSE) : notebook, 3.7.
3. Construis les chunks : ligne de contexte et transcription, avec le chemin de l'image et la page dans le payload.
4. **Vérifie dix transcriptions à la main**, de types différents. Compte les nombres et les noms faux, et note le résultat dans le rapport.
5. Sur les questions `scan_ocr`, compare le VLM et l'OCR de Docling (qualité et temps) : deux expériences.
6. Bonus : afficher l'image sous la réponse (notebook, 3.9).

À mesurer : `image_only`, `scan_ocr`, `image_in_document`, et le temps total de lecture des images.

## 4. Section 7 : le temps et les versions (`feat/versions` → `v0.6-versions`)

C'est la section qui pèse le plus sur la note. Ton point de départ : un passage piège remonte dans le top 5 pour 7 questions sur 17 (`trap_hit`), et 1 réponse sur 17 reprend la valeur du piège. Teste une piste à la fois, de la moins chère à la plus chère :
1. Un filtre `must_not` sur `status` (projet, copie, modèle…). `status` a déjà un payload index.
2. Des consignes au LLM : la décision la plus récente prime, un projet de PV ne fait pas foi, un PV corrigé est remplacé par celui qui le corrige.
3. Les chunks triés par date dans le prompt, chacun avec sa date.
4. Une date de référence extraite de la question par le LLM, puis un filtre `doc_date <= date` appliqué par le code. `doc_date` est déjà indexé.
5. Plus de candidats avant le reranking pour les questions sur un fil de décision.
6. Si tu as le temps : mettre les décisions et le suivi des actions du CODIR dans PostgreSQL, et répondre aux questions `action_tracking` en SQL.

À mesurer : `decision_current`, `decision_history`, `board_resolution`, `version_trap`, `action_tracking`, et le taux de pièges avant et après.

## 5. Section 8 : l'évaluation finale (`v1.0`)

1. Choisis la meilleure configuration sur le jeu de développement : qualité, temps de réponse et coût de l'indexation.
2. Le runner ne charge que le jeu de développement ([runner.py:22-25](src/calorvia_rag/evaluation/runner.py#L22-L25)). Ajoute un mode `test` qui ne charge que les 31 questions de la réserve, commite-le, puis lance-le **une seule fois**, avec le juge.
3. Réexporte PostgreSQL dans `results/*.csv` et commite. Fusionne dans `main`, pose le tag `v1.0` et lance `git push origin --tags`.

## 6. Le RAPPORT.md

Remplis les sections 4 à 7 sur le modèle de la section 3, puis ajoute :
- le taux de pièges avant et après la section 7 ;
- le temps total de lecture des images et le taux d'erreur sur les dix transcriptions ;
- ce qui n'a rien changé ou a dégradé les résultats ;
- les scores de la réserve de test, comparés au jeu de développement ;
- trois questions ratées par la configuration finale. Pour chacune, l'étape où l'échec se situe (inventaire, conversion, chunking, recherche, reranking, génération) et une piste de correction.

## 7. Le README et la reproductibilité

- Ajoute les nouvelles commandes : la transcription par le VLM et le mode `test`.
- Nettoie [pyproject.toml](pyproject.toml) : la `description` est encore celle par défaut, et `[project.scripts]` pointe vers un module `20_calorvia_rag_1` qui n'existe pas.
- Teste un clone propre dans un dossier vide : `uv sync`, l'ingestion, puis une expérience.

## 8. La démonstration (5 minutes)

La question est écrite en dur dans [ask.py](src/calorvia_rag/rag/ask.py#L52-L58). Fais-lui lire la question en argument, ou ajoute une petite interface. Prépare trois questions, dont une dont la réponse vient d'une image, et répète. Les exemples de l'énoncé conviennent bien : la date de démarrage de l'ERP, l'action A-26-008, la vitesse à Gand.

## Pendant tout le projet

- Une branche par section, fusionnée dans `main` une fois évaluée, puis le tag poussé sur GitHub.
- Une expérience citée dans le rapport doit tourner sur du code commité (`git_dirty = false`). Ensuite : le juge, puis l'export CSV.
- Des messages de commit en anglais et à l'impératif, par exemple `Add per-language BM25 stemmer` plutôt que `change rapport.md`.

**Le minimum obligatoire** est une expérience par section, de 4 à 7. Si le temps manque, ne saute pas la section 6 (la démo doit montrer une réponse tirée d'une image) ni la section 7 (c'est elle qui fait la différence).

Si tu veux, je commence par l'étape 1 : le stemmer selon la langue.
