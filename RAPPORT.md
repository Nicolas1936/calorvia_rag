# Rapport : RAG documentaire Calorvia

## Méthode

- **Jeu de développement** : 127 questions, dont 122 avec une réponse dans le corpus et 5 hors corpus (`out_of_corpus`). La réserve de test (31 questions, `id % 5 == 0`) n'a pas été utilisée.
- **Un changement à la fois** : chaque expérience modifie un seul réglage par rapport à la référence et tourne sur un code commité (`git_dirty = false`).
- **Numérotation** : le « # » du tableau est l'identifiant de l'expérience dans la base, dans l'ordre de lancement. Le nom (`exp01_…`, `exp02_…`) est celui de son fichier de configuration dans `experiments/`.

### Métriques

| Métrique | Ce qu'elle mesure | Calculée sur |
|---|---|---|
| hit@5 | Au moins un passage de preuve figure parmi les 5 passages retenus | 122 questions |
| MRR | Rang du premier passage de preuve : 1 s'il est 1er, 1/2 s'il est 2e, 1/3 s'il est 3e… | 122 questions |
| recall@5 | Part des passages de preuve retrouvés dans le top 5, quand une question en a plusieurs | 122 questions |
| nDCG@5 | Qualité du classement, en tenant compte du grade de chaque preuve | 122 questions |
| Refus à tort | Le modèle répond qu'il ne sait pas alors que la réponse est dans le corpus | 122 questions |
| correctness | Note du juge (0 à 1) : la réponse est-elle juste et complète par rapport à la réponse attendue ? | Échantillon du juge (31 questions) |
| faithfulness | Note du juge (0 à 1) : la réponse s'appuie-t-elle uniquement sur les passages retrouvés ? | Échantillon du juge (31 questions) |
| trap_hit | Un passage piège (valeur fausse ou périmée) figure dans le top 5 | 17 questions avec piège |
| Pièges repris | Après relecture, la réponse donne la valeur piège | 17 questions avec piège |

Un passage compte comme preuve s'il vient du document attendu et contient tous les extraits de la preuve. hit@5, MRR et recall@5 ne comptent que les preuves de grade 2 ou plus. nDCG@5 les compte toutes, pondérées par leur grade.

## Tableau comparatif des expériences

| # | Expérience | Commit | Changement | hit@5 | MRR | recall@5 | nDCG@5 | Refus à tort | correctness | Pièges repris | Durée |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 3 | `exp01_baseline_no_ctx` | `fa951e7` | Version de référence, sans ligne de contexte | 0,746 | 0,602 | 0,713 | 0,611 | 18,0 % | 0,54 | 2/17 | 267 s |
| **1** | **`exp02_baseline_with_ctx`** | **`da85aca`** | **+ ligne de contexte** (retenue, `v0.2-baseline`) | **0,787** | **0,708** | **0,762** | **0,697** | **13,9 %** | **0,62** | **1/17** | 281 s |
| 2 | `exp01_baseline_no_ctx` | `da85aca` | Abandonnée (`superseded`) : lancée avec `git_dirty = true`, puis relancée en n° 3 | – | – | – | – | – | – | – | – |
| 4 | `exp03_stemmer_per_language` | `156554b` | Référence + stemmer BM25 selon la langue du chunk (index `_lang`) | 0,787 | 0,708 | 0,762 | 0,697 | 13,9 % | 0,62 | 1/17 | 275 s |
| 5 | `exp04_translate_query` | `6fd79d3` | Abandonnée (`failed`) : échec au démarrage (0 réponse en 6 s), relancée en n° 6 | – | – | – | – | – | – | – | – |
| 6 | `exp04_translate_query` | `6fd79d3` | n° 4 + traduction de la question en nl/en, 6 listes fusionnées par RRF | 0,787 | 0,708 | 0,762 | 0,697 | 14,8 % | 0,62 | 1/17 | 407 s |
| 7 | `exp05_rerank_per_language` | `ee0e6fe` | n° 6 + reranking de chaque passage avec la question dans sa langue (abandonné avec la traduction) | 0,779 | 0,705 | 0,754 | 0,694 | 16,4 % | 0,61 | 1/17 | 422 s |
| 8 | `exp06_prompt_french` | `1ed0698` | Abandonnée (`superseded`) : lancée avec `git_dirty = true` (prompt et TOML pas encore commités), puis relancée en n° 9 | – | – | – | – | – | – | – | – |
| **9** | **`exp06_prompt_french`** | **`530973a`** | **n° 4 + prompt « réponds en français même si le passage est en néerlandais ou en anglais »** (retenue, `v0.3-langues`) | **0,787** | **0,708** | **0,762** | **0,697** | **14,8 %** | **0,62** | **1/17** | 272 s |
| 10 | `exp07_excel_openpyxl` | `3b024a1` | n° 9 + classeurs lus par openpyxl, une phrase par ligne de tableau (index `_xlsx`, retenue) | 0,787 | 0,706 | 0,758 | 0,694 | 14,8 % | 0,61 | 1/17 | 247 s |
| 11 | `exp08_images_vlm` | `4546dab` | Abandonnée (`superseded`) : juge interrompu après 10 notes sur 31, relancée en n° 12 | – | – | – | – | – | – | – | – |
| 12 | `exp08_images_vlm` | `4546dab` | n° 10 + images et scans transcrits par le VLM (index `_img_scan`, retenue) | 0,934 | 0,839 | 0,910 | 0,831 | 4,1 % | 0,75 | 0/17 | 267 s |
| 13 | `exp09_scans_docling_ocr` | `b90f2e8` | Abandonnée (`failed`) : lancée avec `git_dirty = true`, arrêtée au démarrage (0 réponse en 11 s), relancée en n° 14 | – | – | – | – | – | – | – | – |
| 14 | `exp09_scans_docling_ocr` | `1d0d1da` | n° 12, mais les 26 documents numérisés (scans, factures, bons de livraison) sont lus par l'OCR de Docling au lieu du VLM (index `_ocr`, non retenue) | 0,918 | 0,818 | 0,898 | 0,814 | 4,1 % | 0,73 | 0/17 | 248 s |
| 15 | `exp10_pdf_charts` | `33e9482` | n° 12 + graphiques des PDF texte transcrits par le VLM (index `_pdfimg`, retenue) | 0,943 | 0,847 | 0,918 | 0,839 | 3,3 % | 0,78 | 0/17 | 266 s |
| 16 | `exp11_exclude_drafts` | `6010c97` | n° 15 + filtre `must_not` sur le statut `projet` (projets de PV du CA, projet de tarif), registre corrigé (retenue) | 0,943 | 0,855 | 0,918 | 0,845 | 3,3 % | 0,78 | 0/17 (1 cas limite : Q023) | 268 s |
| 17 | `exp12_prompt_versions` | `ec9f7b9` | n° 16 + consignes sur les versions dans le prompt : projet, PV corrigé, date passée (retenue) | 0,943 | 0,855 | 0,918 | 0,845 | 3,3 % | 0,77 | 0/17 | 271 s |

- La durée est celle du run complet (127 questions).
- Le modèle a refusé toutes les questions `out_of_corpus` (5/5), dans toutes les expériences.

## Section 3 : version de référence (`v0.2-baseline`)

### Configuration

- **Corpus** : documents qui contiennent du texte (PDF natifs, DOCX, HTML, PPTX, MD, CSV, XLSX), convertis par Docling sans OCR. Les images et les scans ne sont pas encore lus.
- **Chunking** : `HybridChunker` limité à 512 tokens (tokenizer bge-m3). La ligne de contexte (type de document, date, dossier) est ajoutée en tête de chaque chunk.
- **Recherche** : recherche hybride dans Qdrant (bge-m3 dense + BM25), 30 candidats, reranker `bge-reranker-v2-m3`, top 5.
- **Génération** : `qwen3.8-27b`, prompt `prompts/detailed.txt`.
- **Juge** : `gemma-4-26b`, échantillon de 31 questions (2 par type, graine 42).

### Le changement testé : la ligne de contexte

L'expérience 3 indexe chaque chunk seul. L'expérience 1 ajoute en tête de chaque chunk une ligne qui donne le type du document, sa date, sa version et son dossier :

```
[PV du CODIR du 17 novembre 2025 (v2) · 00_Direction/CODIR/2025]
```

Sans cette ligne, deux versions d'un même document, ou les PV de deux séances différentes, donnent des chunks presque identiques. La ligne permet de les distinguer, à la recherche comme à la génération. Elle est rédigée en français, avec la date en toutes lettres, comme dans les questions.

### Comparabilité des deux expériences

Les expériences 1 et 3 ont tourné sur des commits différents. Entre `da85aca` et `fa951e7`, seuls le code du juge, le fichier de configuration par défaut et les versions de `deepeval` et `transformers` ont changé. La recherche, le prompt et l'index sont identiques. L'expérience 3 obtient d'ailleurs, question par question, le même hit@5 que l'expérience 2. Les scores du juge des deux expériences ont été recalculés avec le juge du commit `79200be`.

### Résultats globaux (sans → avec ligne de contexte)

Les sept indicateurs de qualité progressent :

- la recherche trouve une preuve pour 96 questions sur 122, contre 91 (hit@5 de 0,746 à 0,787), et retrouve une plus grande part des preuves quand une question en a plusieurs (recall@5 de 0,71 à 0,76) ;
- la preuve est mieux classée (MRR de 0,60 à 0,71, nDCG@5 de 0,61 à 0,70) ;
- le modèle refuse à tort 17 questions au lieu de 22 (13,9 % contre 18,0 %) ;
- les réponses sont plus justes (correctness de 0,54 à 0,62), et une réponse de moins reprend un piège (1/17 contre 2/17).

Le run complet prend 14 s de plus (+5 %).

### Résultats par type de question (sans → avec ligne de contexte)

| Type | n | hit@5 | MRR | Refus | correctness (n = 2) |
|---|---|---|---|---|---|
| factual | 16 | 0,94 → 0,94 | 0,81 → 0,91 | 0,06 → 0,06 | 0,80 → 0,80 |
| decision_current | 14 | 0,86 → 0,79 | 0,70 → 0,67 | 0,00 → 0,00 | 0,70 → 0,60 |
| excel_lookup | 13 | 0,92 → 0,92 | 0,74 → 0,85 | 0,08 → 0,08 | 0,55 → 0,55 |
| image_only | 13 | 0,00 → 0,00 | 0,00 → 0,00 | 0,77 → 0,69 | 0,00 → 0,00 |
| action_tracking | 11 | 1,00 → 1,00 | 0,95 → 1,00 | 0,00 → 0,00 | 0,30 → 0,55 |
| meeting_detail | 10 | 0,80 → 1,00 | 0,58 → 0,85 | 0,10 → 0,00 | 0,50 → 0,85 |
| multilingual | 7 | 0,57 → 0,86 | 0,48 → 0,69 | 0,43 → 0,00 | 0,25 → 0,70 |
| board_resolution | 6 | 0,83 → 0,83 | 0,64 → 0,71 | 0,00 → 0,00 | 0,45 → 0,60 |
| decision_history | 6 | 1,00 → 1,00 | 0,68 → 1,00 | 0,17 → 0,00 | 0,75 → 0,70 |
| scan_ocr | 6 | 0,17 → 0,17 | 0,17 → 0,17 | 0,67 → 0,67 | 0,35 → 0,35 |
| decision_reason | 5 | 1,00 → 1,00 | 0,80 → 0,90 | 0,00 → 0,00 | 0,90 → 0,90 |
| excel_reasoning | 5 | 0,60 → 1,00 | 0,50 → 0,64 | 0,00 → 0,00 | 0,55 → 0,85 |
| multi_doc | 5 | 1,00 → 1,00 | 0,74 → 1,00 | 0,00 → 0,20 | 0,80 → 0,50 |
| out_of_corpus | 5 | – | – | 1,00 → 1,00 (attendu) | 1,00 → 1,00 |
| version_trap | 4 | 1,00 → 1,00 | 0,56 → 0,81 | 0,00 → 0,00 | 0,50 → 0,65 |
| image_in_document | 1 | 0,00 → 0,00 | 0,00 → 0,00 | 1,00 → 1,00 | 0,00 → 0,00 |

**Lecture :**
- Les questions `image_only`, `image_in_document` et `scan_ocr` échouent dans les deux expériences, comme prévu : ces documents ne sont pas encore lus, et la ligne de contexte ne peut rien quand le texte n'est pas indexé. Pour `image_only`, le modèle refuse 9 questions sur 13 et répond aux 4 autres sans le document qui contient la réponse. Ces 4 réponses sont à vérifier.
- La ligne de contexte aide surtout pour `multilingual` (hit@5 de 0,57 à 0,86, refus de 43 % à 0 %). Les questions sont en français et les documents en néerlandais ou en anglais : la ligne, en français, ajoute probablement aux chunks des mots de la question (type de document, date). Elle aide aussi pour `excel_reasoning` (hit@5 de 0,60 à 1,00) et `meeting_detail` (hit@5 de 0,80 à 1,00).
- Elle améliore le classement (MRR) pour `decision_history`, `version_trap` et `multi_doc` : la date et le type du document permettent de distinguer des documents qui se ressemblent.
- `action_tracking`, `excel_lookup` et `multi_doc` trouvent le bon document (hit@5 ≥ 0,92), mais les réponses jugées sont souvent incomplètes (correctness autour de 0,55). Le problème viendrait alors de la génération ou de la taille des chunks, pas de la recherche. Avec 2 réponses jugées par type, c'est un indice à confirmer.

### Résultats par format de document (sans → avec ligne de contexte)

Le format retenu pour une question est celui de son document de preuve principal (celui qui a le grade le plus élevé). Il vient de la table `documents`.

| Format | n | hit@5 | MRR | Refus | correctness (n) |
|---|---|---|---|---|---|
| DOCX | 51 | 0,92 → 0,96 | 0,75 → 0,89 | 0,08 → 0,02 | 0,64 → 0,74 (10) |
| PDF natif | 24 | 0,79 → 0,83 | 0,64 → 0,76 | 0,12 → 0,04 | 0,53 → 0,69 (7) |
| XLSX | 19 | 0,84 → 0,95 | 0,63 → 0,76 | 0,05 → 0,05 | 0,56 → 0,68 (5) |
| Image | 19 | 0,16 → 0,16 | 0,16 → 0,16 | 0,63 → 0,58 | 0,17 → 0,17 (4) |
| Scan | 5 | 0,40 → 0,40 | 0,27 → 0,25 | 0,40 → 0,60 | 0,40 → 0,10 (2) |
| HTML | 2 | 1,00 → 1,00 | 1,00 → 1,00 | 0,00 → 0,00 | – |
| PPTX | 1 | 1,00 → 1,00 | 0,50 → 1,00 | 0,00 → 0,00 | 0,40 → 0,70 (1) |
| MD | 1 | 1,00 → 1,00 | 1,00 → 1,00 | 0,00 → 0,00 | – |
| Hors corpus | 5 | – | – | 1,00 → 1,00 | 1,00 → 1,00 (2) |

Pour les images et les scans, les quelques hits viennent d'un autre document de preuve de la même question, qui contient du texte.

### Pièges

| | Sans ligne | Avec ligne |
|---|---|---|
| `trap_hit` : un passage piège apparaît dans le top 5 | 7/17 (0,41) | 7/17 (0,41) |
| `trap_avoided` selon le juge | 13/17 (0,76) | 15/17 (0,88) |
| **Réponses qui reprennent le piège, après relecture** | **2/17** (Q023, Q153) | **1/17** (Q023) |

- Q023 : la réponse donne 1,2 M€, la valeur du piège, dans les deux expériences.
- Q153 : sans ligne de contexte, la réponse donne 190 M€, la valeur de l'ancien plan. Avec la ligne, elle donne la bonne valeur.
- Le piège arrive dans le top 5 pour 41 % des questions concernées, mais le modèle le reprend rarement. La date et la version qui figurent dans la ligne de contexte l'aident à choisir le bon document. Ce taux sert de point de comparaison pour la section 7.

### Ce qui n'a rien changé, ou a dégradé les résultats

- La ligne de contexte ne change ni `trap_hit` (les passages pièges restent dans le top 5) ni `faithfulness` (0,87 dans les deux cas).
- `decision_current` : hit@5 passe de 0,86 à 0,79, une question perdue sur 14.
- `multi_doc` : une question sur 5 est refusée avec la ligne de contexte, alors qu'aucune ne l'était sans.
- La durée du run passe de 267 s à 281 s (+5 %).

Les deux dégradations portent chacune sur une seule question. À cette taille d'échantillon, elles peuvent relever du bruit.

### Limites de l'évaluation

- **Échantillon du juge** : 2 questions par type, donc la correctness par type ne repose que sur 2 réponses. Seule la moyenne globale (31 questions) est interprétable.
- **`faithfulness`** pénalise des réponses justes de `decision_history` (Q002, Q052) qui retracent l'historique d'une décision. Pour ce type, je m'appuie sur `correctness`.
- **`trap_avoided`** : le juge se trompe sur 1 à 2 questions sur 17. Pour Q008, la réponse est incomplète mais ne donne pas la valeur piège, et aucune étape des consignes du juge ne couvre ce cas. Pour Q027 (sans ligne de contexte), le juge note 0 une réponse juste. C'est pourquoi le taux de pièges retenu est celui de la relecture manuelle.
- **Plafond du texte seul** : sur les 217 passages de preuve du jeu de développement, 177 se trouvent dans le texte indexé. Les 40 autres sont dans des images (29), des scans (7) ou un graphique (1), dans des doublons exclus mais couverts par la copie conservée (2), ou dans `02_RH/Confidentiel`, que l'inventaire exclut (1, Q154).

### Décision : la ligne de contexte est retenue

1. **La comparaison est équitable** : seule la ligne de contexte change entre les deux expériences. La recherche, le prompt et l'index sont identiques, et les deux runs sont notés par le même juge.
2. **Tous les indicateurs de qualité progressent ensemble** : la recherche (hit@5, MRR, recall@5, nDCG@5), les refus à tort, la correctness globale et les pièges repris.
3. **Les gains s'expliquent** : ils portent sur les types où la langue, la date ou le type du document aident (`multilingual`, `version_trap`, `decision_history`). Ils sont nuls là où le texte n'est pas indexé (images, scans).
4. **Les pertes sont faibles** : une question en `decision_current`, un refus en `multi_doc` et 14 s de calcul.

L'expérience 1 devient la référence `v0.2-baseline`. Les sections 4 à 7 lui sont comparées.

### Points de départ des sections suivantes

- **Section 4 (langues)** : `multilingual` reste en dessous des autres types textuels (hit@5 de 0,86, MRR de 0,69).
- **Section 5 (Excel)** : `excel_lookup` trouve le bon classeur (hit@5 de 0,92), mais les réponses jugées restent incomplètes.
- **Section 6 (images et scans)** : 40 des 217 passages de preuve ne sont pas dans le texte indexé. `image_only`, `image_in_document` et `scan_ocr` ont un hit@5 compris entre 0 et 0,17.
- **Section 7 (versions)** : les passages pièges restent dans le top 5 pour 7 questions sur 17. La ligne de contexte aide le modèle à choisir la bonne version, mais elle ne les écarte pas. Taux de départ : 1/17 réponse reprend le piège.

## Section 4 : les langues (`v0.3-langues`)

Les questions sont toutes en français. L'index contient 1 072 chunks en français, 94 en néerlandais et 18 en anglais : la langue est détectée pour chaque chunk et enregistrée dans le payload. La section teste un changement par expérience. Chacun est ajouté à la dernière configuration retenue, en partant de la référence `v0.2-baseline` (n° 1) :

1. le stemmer BM25 choisi selon la langue du chunk (n° 4, retenu) ;
2. la traduction de la question en néerlandais et en anglais (n° 6, gardée à l'essai) ;
3. le reranking de chaque passage avec la question dans sa langue (n° 7), ajouté après le diagnostic de l'étape 2. Il est abandonné, et la traduction avec lui ;
4. un prompt qui impose une réponse en français (n° 9, retenu), ajouté à la configuration n° 4.

### Étape 1 : le stemmer BM25 selon la langue du chunk (n° 4)

#### Le changement testé

Dans la référence, la recherche lexicale (BM25, calculé par Qdrant) applique le stemmer et les mots vides `french` à tous les chunks, y compris aux chunks néerlandais et anglais. L'expérience 4 prend à l'indexation la langue de chaque chunk : `fr` → `french`, `nl` → `dutch`, `en` → `english`. La question, toujours en français, garde le stemmer `french`.

Le réglage s'active dans le TOML (`[index] sparse_language = 'per_chunk'`) et ajoute le suffixe `_lang` au nom de la collection (`bge-m3_hybrid_512_ctx_bm25_lang`). L'index de la référence est donc conservé.

#### Vérification de l'index

Qdrant accepte sans erreur un nom de langue inconnu : `klingon` donne une analyse sans stemmer ni mots vides. Une faute de frappe dans le nom d'une langue passerait donc inaperçue. Pour vérifier que `dutch` et `english` sont bien appliqués, j'ai lancé des requêtes faites uniquement de mots vides, analysées avec `klingon` pour qu'aucun mot ne soit retiré de la requête :

| Requête | Référence (`french` partout) | Expérience 4 (`_lang`) |
|---|---|---|
| `het een van zijn niet` (néerlandais) | 81 chunks | 15 chunks |
| `the and of with from` (anglais) | 19 chunks | 0 chunk |

Dans l'index `_lang`, les chunks néerlandais et anglais ne contiennent plus leurs mots vides. Les 15 chunks restants sont tous classés en français (des COPIL du projet Atlas, pour la plupart) : ils contiennent l'un de ces mots, sans doute dans un nom propre.

#### Comparabilité

Entre les commits `da85aca` (n° 1) et `156554b` (n° 4), en dehors de ce changement, seuls le code du juge, le fichier de configuration par défaut et les versions de `deepeval` et `transformers` ont changé, comme pour l'expérience 3. Les deux expériences sont notées par le même code de juge (celui du commit `79200be`). Le top 5 est identique, dans le même ordre, pour 122 questions sur 127.

#### Résultats (référence → stemmer par langue)

| | Référence (n° 1) | Stemmer par langue (n° 4) |
|---|---|---|
| hit@5 | 0,787 | 0,787 |
| MRR | 0,708 | 0,708 |
| recall@5 | 0,762 | 0,762 |
| nDCG@5 | 0,697 | 0,697 |
| Refus à tort | 17/122 (13,9 %) | 17/122 (13,9 %) |
| correctness (31) | 0,619 | 0,616 |
| faithfulness (31) | 0,871 | 0,871 |
| `trap_hit` | 7/17 | 7/17 |
| `trap_avoided` selon le juge | 15/17 (0,88) | 15/17 (0,88) |
| Réponses qui reprennent le piège, après relecture | 1/17 (Q023) | 1/17 (Q023) |
| Temps de réponse moyen / médian | 6,45 s / 6,24 s | 6,41 s / 5,99 s |
| Durée du run | 281 s | 275 s |

Par type de question, aucun hit@5, MRR ou taux de refus ne change, sauf le MRR de `excel_reasoning`, qui passe de 0,64 à 0,65 (Q158 : de 0,20 à 0,25). Le top 5 change pour 5 questions (Q021, Q031, Q059, Q074, Q158), sans effet sur les métriques, sauf pour Q158.

#### Les questions `multilingual`

Rien ne change pour ce type. Le tableau sert de point de départ pour l'étape 2 :

| Question | Document de preuve | Langue | Rang de la preuve |
|---|---|---|---|
| Q003 : chiffre d'affaires et EBITDA 2025 | `2026-03-19 PR 2025 results.docx` | en | 1 |
| Q024 : contrat de maintenance des chariots de Gand | `Onderhoudscontract heftrucks LiftService.pdf` | nl | 2 |
| Q062 : causes de l'accident de Gand | `Incidentrapport 2025-11-12 heftruck gang 7.pdf` | nl | **absent du top 5** |
| Q074 : délai de livraison de Kompra | `Supply agreement Kompra GmbH 2024-2026.pdf` | en | 1 |
| Q083 : objectif de chiffre d'affaires avec Klimaat Partners | `Accountplan Klimaat Partners 2026.docx` | nl | 1 |
| Q086 : part des coûts d'un rappel supportée par Valtek | `Supply agreement Valtek Components 2025.pdf` | en | 3 |
| Q112 : absentéisme de Gand en mars 2026 | `Verslag Comite PBW Gent 2026-04-16.docx` | nl | 1 |

Le seul échec, Q062, porte sur un rapport néerlandais qui ne partage aucun mot avec la question : seule la recherche dense peut le trouver, et elle ne le classe pas assez haut. Q024 et Q086 trouvent leur preuve, mais pas en première position.

#### Pourquoi rien ne change

- La question reste en français et analysée avec le stemmer `french`. Un mot français ne correspond pas plus qu'avant à un mot néerlandais ou anglais : la partie BM25 de la recherche ne trouve toujours pas les chunks des autres langues, qui n'arrivent que par la recherche dense.
- Le changement ne touche que la façon dont 112 chunks (9 % de l'index) sont découpés en mots.
- Un risque ne s'est pas réalisé : la ligne de contexte est en français, mais elle est maintenant analysée avec le stemmer néerlandais dans les chunks néerlandais. Ses mots auraient pu ne plus correspondre à ceux de la question. Or la section 3 a montré que cette ligne aide justement les questions `multilingual`. Les résultats de ce type sont pourtant inchangés.

#### Bruit de mesure

Cette expérience donne une mesure du bruit, puisque le top 5 est presque identique à celui de la référence :

- **La génération n'est pas déterministe** : la température vaut 0, pourtant 12 réponses sur 127 diffèrent, dont 10 avec exactement le même top 5. Cause probable : llama.cpp traite 3 requêtes en parallèle, et la façon dont il les regroupe modifie légèrement les calculs. Les 3 écarts de correctness (Q021 : +0,1, Q024 : −0,1, Q042 : −0,1) portent tous sur ces réponses reformulées.
- **Le juge varie aussi** : avec des réponses identiques, la faithfulness de Q116 passe de 1 à 0, et celle de Q144 de 0 à 1.
- **Le juge peut échouer** : pour Q008, Gemma a renvoyé un JSON invalide (`DeepEvalError`). La note était vide, et la moyenne de `trap_avoided`, calculée sur 16 questions seulement, montait à 0,94. Q008 a été rejugée seule et obtient 0, comme dans la référence.

Sur les 31 questions jugées, un écart de 0,03 correspond à une seule note qui passe de 1 à 0. Un écart de cet ordre n'est pas interprétable.

#### Décision : le stemmer par langue est conservé

Il ne change aucun résultat et ne coûte rien à la recherche. Surtout, il prépare l'étape 2 : une question traduite en néerlandais, analysée avec le stemmer `dutch`, pourra retrouver par BM25 les chunks néerlandais analysés avec le même stemmer. Les expériences suivantes de la section utilisent donc l'index `_lang`.

### Étape 2 : traduction de la question (n° 6)

#### Le changement testé

Avant la recherche, le LLM de génération (`qwen3.8-27b`, température 0, sans raisonnement, sortie JSON) traduit la question en néerlandais et en anglais (`rag/translate.py`, prompt repris du notebook, partie 1.3). La recherche hybride utilise ensuite les trois versions de la question. Pour chacune, elle construit une liste dense (bge-m3) et une liste BM25 analysée avec le stemmer de sa langue. Les six listes sont fusionnées par RRF (k = 60) en 30 candidats. Le reranker trie ensuite ces candidats avec la question française, comme dans la référence.

Le réglage s'active dans le TOML (`[search] translate_query = true`) et utilise l'index `_lang` de l'étape 1. Si la réponse du LLM n'est pas un JSON valide, la recherche se fait avec la question française seule.

Exemple, Q062 :

| Langue | Question |
|---|---|
| fr | Quelles causes de l'accident de Gand le rapport d'incident identifie-t-il ? |
| nl | Welke oorzaken van het ongeluk van Gent identificeert het incidentrapport? |
| en | Which causes of the Ghent accident does the incident report identify? |

Le LLM a traduit « Gand » par « Gent », le nom employé dans les documents néerlandais, alors que la consigne demande de garder les noms propres tels quels. Ici, ça aide la recherche.

#### Comparabilité

Entre les commits `156554b` (n° 4) et `6fd79d3` (n° 6), seuls le rapport et le code de la traduction ont changé. L'index est le même.

#### Résultats (stemmer par langue → + traduction)

| | Stemmer par langue (n° 4) | + traduction (n° 6) |
|---|---|---|
| hit@5 | 0,787 | 0,787 |
| MRR | 0,708 | 0,708 |
| recall@5 | 0,762 | 0,762 |
| nDCG@5 | 0,697 | 0,697 |
| Refus à tort | 17/122 (13,9 %) | 18/122 (14,8 %) |
| correctness (31) | 0,616 | 0,616 |
| faithfulness (31) | 0,871 | 0,774 |
| `trap_hit` | 7/17 | 7/17 |
| `trap_avoided` selon le juge | 15/17 (0,88) | 15/17 (0,88) |
| Réponses qui reprennent le piège, après relecture | 1/17 (Q023) | 1/17 (Q023) |
| Temps de réponse moyen / médian / 90e centile | 6,41 s / 5,99 s / 10,5 s | **9,51 s / 9,16 s / 13,3 s** |
| Durée du run | 275 s | **407 s (+48 %)** |

La traduction ne change rien à la qualité de la recherche. Le top 5 change pour 27 questions, mais jamais à la position de la preuve : hit@5, MRR et nDCG@5 restent identiques pour chaque question, sauf pour Q158, dont le MRR revient à sa valeur de la référence (de 0,25 à 0,20). Les passages néerlandais et anglais du top 5 passent de 26 à 30, sur 635. Les 7 questions `multilingual` gardent le même rang de preuve qu'à l'étape 1 : Q062 reste absente du top 5.

#### Diagnostic : le reranker défait le gain de la recherche

Pour Q062, la recherche fait son travail : l'`Incidentrapport` arrive 1er et 5e des 30 candidats après la fusion RRF. Le reranker, lui, compare ces candidats à la question française. Voici le rang du même rapport quand on donne au reranker chacune des trois versions de la question :

| Question donnée au reranker | Rang de l'`Incidentrapport` | Son score | Score du 1er passage français |
|---|---|---|---|
| fr | 7e et 10e | 0,057 | 0,693 |
| nl | **1er et 2e** | **0,523** | 0,011 |
| en | **1er et 2e** | **0,466** | 0,010 |

bge-reranker-v2-m3 est multilingue, mais il favorise nettement les passages écrits dans la langue de la question : le même passage obtient 0,057 avec la question française et 0,523 avec la question néerlandaise. Les candidats néerlandais et anglais ajoutés par la traduction passent donc derrière les passages français, et le top 5 final reste presque le même.

La réponse à Q062 est quand même juste (absence de passage piéton, visibilité réduite à l'angle des racks, chariot à environ 11 km/h). Elle s'appuie sur le *Projet PV CA* du 18 novembre 2025, qui résume le rapport d'incident. Mais c'est un projet de PV (voir la section 7), et hit@5 ne compte comme preuve que le rapport lui-même.

#### Les autres changements

- **Q077** (« conditions de paiement de Calorvia ») : la preuve (`Conditions generales de vente 2026.pdf`) n'est dans le top 5 ni avant ni après. Avant, le modèle donnait les conditions de paiement d'offres de **fournisseurs** (30 / 60 / 10 %) : une réponse fausse. Maintenant, il refuse. Le refus compte « à tort », mais il vaut mieux qu'une réponse fausse.
- **faithfulness** : la baisse de 0,871 à 0,774 vient de 3 notes qui passent de 1 à 0. Pour Q082 et Q144, la réponse est identique à celle de l'expérience 4 : c'est le juge qui varie (la note de Q144 change à chaque run). Pour Q153, le top 5 est le même et seule la formulation de la réponse change. Cette baisse relève du bruit décrit à l'étape 1.
- **Pièges** : 13 réponses sur 17 sont identiques. Les 4 autres ne donnent pas la valeur piège.

#### Coût

Chaque question coûte un appel de plus au LLM, avant la recherche. Le temps de réponse moyen augmente de 3,1 s (+48 %), et la durée du run passe de 275 s à 407 s. Ce surcoût vient probablement surtout de cet appel : les quatre recherches de plus sont faites dans la même requête Qdrant, et les trois embeddings dans le même appel à l'embedder.

#### Décision : la traduction est gardée pour l'étape suivante, à l'essai

Seule, la traduction coûte 3 s par question sans rien améliorer. Le diagnostic montre pourtant que la recherche trouve les bons passages et que le problème se situe au reranking. L'étape 3 garde donc la traduction et compare chaque passage à la question dans sa langue. Si cette étape n'apporte rien non plus, la traduction sera abandonnée.

### Étape 3 : reranker chaque passage avec la question dans sa langue (n° 7)

#### Le changement testé

La recherche est celle de l'étape 2 : trois versions de la question, six listes fusionnées par RRF en 30 candidats. Les candidats sont ensuite répartis selon la langue de leur chunk, et le reranker trie chaque groupe avec la question dans la même langue : les passages néerlandais avec la question néerlandaise, les anglais avec l'anglaise, les français avec la française (`rag/rerank.py`). Les scores des trois groupes sont enfin réunis et triés pour garder les 5 meilleurs passages.

Le réglage s'active dans le TOML (`[reranker] per_language = true`) et n'a d'effet que si `translate_query` est activé. Un passage dont la langue n'a pas de traduction est comparé à la question française.

#### Comparabilité

Entre les commits `6fd79d3` (n° 6) et `ee0e6fe` (n° 7), seuls le rapport, le code du reranking et son appel dans `rag/ask.py` ont changé. L'index et la recherche sont les mêmes.

#### Résultats (stemmer par langue → + traduction → + reranking par langue)

| | Stemmer par langue (n° 4) | + traduction (n° 6) | + reranking par langue (n° 7) |
|---|---|---|---|
| hit@5 | 0,787 | 0,787 | 0,779 |
| MRR | 0,708 | 0,708 | 0,705 |
| recall@5 | 0,762 | 0,762 | 0,754 |
| nDCG@5 | 0,697 | 0,697 | 0,694 |
| Refus à tort | 17/122 (13,9 %) | 18/122 (14,8 %) | **20/122 (16,4 %)** |
| correctness (31) | 0,616 | 0,616 | 0,610 |
| faithfulness (31) | 0,871 | 0,774 | 0,871 |
| `trap_hit` | 7/17 | 7/17 | 7/17 |
| `trap_avoided` selon le juge | 15/17 (0,88) | 15/17 (0,88) | 15/17 (0,88) |
| Réponses qui reprennent le piège, après relecture | 1/17 (Q023) | 1/17 (Q023) | 1/17 (Q023) |
| Temps de réponse moyen / médian / 90e centile | 6,41 s / 5,99 s / 10,5 s | 9,51 s / 9,16 s / 13,3 s | 9,83 s / 9,24 s / 14,4 s |
| Durée du run | 275 s | 407 s | 422 s |

Par rapport à l'expérience 6, le top 5 change pour 27 questions. Les passages néerlandais et anglais du top 5 passent de 30 à 35 sur 635 (néerlandais : de 16 à 24, anglais : de 14 à 11).

#### Les questions `multilingual`

| Question | Langue de la preuve | Rang de la preuve (n° 6) | Rang de la preuve (n° 7) |
|---|---|---|---|
| Q003 : chiffre d'affaires et EBITDA 2025 | en | 1 | 1 |
| Q024 : contrat de maintenance des chariots de Gand | nl | 2 | **absent du top 5** |
| Q062 : causes de l'accident de Gand | nl | absent du top 5 | **2** |
| Q074 : délai de livraison de Kompra | en | 1 | 1 |
| Q083 : objectif de chiffre d'affaires avec Klimaat Partners | nl | 1 | 1 |
| Q086 : part des coûts d'un rappel supportée par Valtek | en | 3 | **1** |
| Q112 : absentéisme de Gand en mars 2026 | nl | 1 | **absent du top 5** |

Le gain attendu se produit pour Q062 : l'`Incidentrapport` arrive 2e et 5e. La réponse s'appuie maintenant sur le rapport lui-même et donne les quatre causes de la réponse attendue, dont la vitesse autorisée de 12 km/h, jugée trop élevée, et l'imprimante d'étiquettes. À l'étape 2, elle n'en donnait que trois, tirées du projet de PV. Q086 gagne aussi deux places.

En revanche, Q024 et Q112 perdent leur preuve, et leurs réponses deviennent des refus. Pour Q024, qui fait partie de l'échantillon du juge, la correctness passe de 0,3 à 0.

#### Diagnostic : pourquoi Q024 et Q112 perdent leur preuve

J'ai relancé le reranker sur les candidats de ces deux questions avec chacune des trois versions de la question. Score du passage de preuve :

| Question donnée au reranker | Q024 : `Onderhoudscontract heftrucks LiftService.pdf` | Q112 : `Verslag Comite PBW Gent 2026-04-16.docx` |
|---|---|---|
| fr | 0,244 | 0,997 |
| nl (celle qu'utilise l'étape 3) | **0,012** | **0,509** |
| en | 0,006 | 0,999 |
| Pour comparer : 5e passage français, avec la question fr | 0,064 | 0,990 |

Avec la question néerlandaise, la preuve passe derrière les cinq meilleurs passages français, notés avec la question française. Il y a deux causes :

1. **La traduction n'emploie pas les mots des documents.** Pour Q112, le passage dit « Absenteïsme in maart 2026: 5,1 % », et la traduction parle de « ziekteverzuimpercentage ». Pour Q024, le contrat parle de « heftrucks », d'« Interventietijd » et de « panne ». La traduction emploie « reachstackers » (un autre type d'engin), « reactietijd » et « storing ». La question française partage plus de mots avec le passage néerlandais (absentéisme, intervention, panne) que sa traduction.
2. **Les scores obtenus avec des questions différentes ne sont pas comparables.** Pour Q112, la question française donne environ 0,99 à tous les PV du CODIR qui citent l'absentéisme global de Calorvia. La question néerlandaise donne au mieux 0,624 à un passage néerlandais. En triant ensemble les scores des trois groupes, l'étape 3 compare des valeurs qui ne sont pas sur la même échelle.

Le biais de langue observé sur Q062 à l'étape 2 n'est donc pas général. Pour Q112, la question française donnait 0,997 au passage néerlandais : la question en français fonctionnait déjà.

#### Les autres changements

- **Q117** (`multi_doc`) : la notice néerlandaise d'Aéris 9 (0,977 avec la question néerlandaise) passe devant la notice française (0,845), et le MRR passe de 1 à 0,5. Les deux notices disent la même chose, mais le jeu d'évaluation ne compte que la française comme preuve. Le classement n'est pas faux : c'est une limite de l'évaluation.
- **Q087** : le communiqué de presse anglais, 1er avec la question française (0,836), passe 3e avec la question anglaise (0,500). La preuve passe ainsi de la 2e à la 1re place (MRR de 0,5 à 1).
- **Q101** : le contrat anglais de Valtek, l'une des preuves, sort du top 5 (recall@5 de 1 à 0,5).
- **faithfulness** : 4 notes repassent de 0 à 1 (Q082, Q116, Q144, Q153). La note de Q024, dont la réponse est devenue un refus, passe de 1 à 0. La faithfulness revient ainsi à sa valeur de l'étape 1, ce qui confirme que sa baisse à l'étape 2 venait du bruit du juge.
- **Pièges** : 12 réponses sur 17 sont identiques. Les 5 autres sont reformulées sans donner la valeur piège.

#### Coût

Le reranker est appelé une fois par langue présente parmi les candidats, au lieu d'une fois. Le temps de réponse moyen augmente de 0,3 s par rapport à l'étape 2, et de 3,4 s par rapport à l'étape 1 : ce surcoût vient surtout de la traduction.

#### Décision : le reranking par langue et la traduction sont abandonnés

L'étape 3 gagne une preuve (Q062) et en perd deux (Q024, Q112). Elle ajoute 3 refus à tort par rapport à l'étape 1, pour 3,4 s de plus par question. Sur 7 questions `multilingual`, ces écarts d'une question ne montrent aucune amélioration. Comme annoncé à l'étape 2, la traduction est donc abandonnée avec le reranking par langue. L'étape 4 part de la configuration n° 4 (stemmer par langue, sans traduction). Le code reste dans le dépôt, désactivé par défaut (`translate_query` et `per_language` absents du TOML).

Piste non testée : reranker chaque passage avec les trois versions de la question et garder le meilleur des trois scores. Sur les trois questions examinées, chaque preuve garderait son meilleur score : 0,244 pour Q024 (fr), 0,999 pour Q112 (en) et 0,523 pour Q062 (nl). Mais cette idée vient de l'examen des résultats du jeu de développement. Elle triplerait aussi les appels au reranker, et 7 questions ne suffiraient pas à la valider.

### Étape 4 : prompt « réponds en français » (n° 9)

#### Le changement testé

Le nouveau prompt `prompts/detailed_fr.txt` est une copie de `prompts/detailed.txt` dont seule la consigne 7 change (à une ligne vide près en fin de fichier) :

> 7. Réponds en français, même si le passage est en néerlandais ou en anglais, en une à trois phrases. Donne les montants, les dates et les valeurs avec leurs unités, tels qu'ils sont écrits dans les documents.

L'ancienne consigne demandait déjà « Réponds en français ». Le changement ne fait qu'y ajouter le cas des passages en néerlandais ou en anglais. Le TOML (`exp06_prompt_french.toml`) reprend celui de l'étape 1 (n° 4), donc sans traduction, et seul `system_prompt` y change.

#### Comparabilité

Le premier run (n° 8) a tourné alors que le prompt et le TOML n'étaient pas encore commités (`git_dirty = true`). Il est marqué `superseded` et a été relancé en n° 9 sur le commit `530973a`. Entre `156554b` (n° 4) et `530973a` (n° 9), en dehors du rapport, seuls le code de la traduction et du reranking par langue (désactivés ici), le nouveau prompt et les TOML ont changé. Le top 5 est identique pour 126 questions sur 127. Seul celui de Q021 change, une question dont le top 5 avait déjà changé entre les n° 1 et 4.

Pour Q002, le juge a renvoyé un JSON invalide, et la note de faithfulness était vide. Elle a été rejugée seule, deux fois, et obtient 1 les deux fois.

#### Résultats (stemmer par langue → + prompt)

| | Stemmer par langue (n° 4) | + prompt « réponds en français » (n° 9) |
|---|---|---|
| hit@5 | 0,787 | 0,787 |
| MRR | 0,708 | 0,708 |
| recall@5 | 0,762 | 0,762 |
| nDCG@5 | 0,697 | 0,697 |
| Refus à tort | 17/122 (13,9 %) | 18/122 (14,8 %) |
| correctness (31) | 0,616 | 0,619 |
| faithfulness (31) | 0,871 | 0,927 |
| `trap_hit` | 7/17 | 7/17 |
| `trap_avoided` selon le juge | 15/17 (0,88) | 15/17 (0,88) |
| Réponses qui reprennent le piège, après relecture | 1/17 (Q023) | 1/17 (Q023) |
| Temps de réponse moyen / médian / 90e centile | 6,41 s / 5,99 s / 10,5 s | 6,35 s / 6,15 s / 10,6 s |
| Durée du run | 275 s | 272 s |

#### La langue des réponses

Le détecteur de langue de l'inventaire classe les 127 réponses en français, dans l'expérience 9 comme dans toutes les précédentes (n° 1, 4, 6 et 7). Les 7 réponses `multilingual` sont identiques ou seulement reformulées. Elles traduisent déjà les faits tirés des passages néerlandais et anglais : pour Q024, « binnen 8 werkuren » devient « 8 heures ouvrées ». Le modèle suivait donc déjà la consigne, et la nouvelle formulation n'a rien à corriger.

#### Les autres changements

- **Réponses reformulées** : 33 réponses changent alors que leur top 5 est le même, contre 10 entre les n° 1 et 4. Changer le prompt modifie le texte que reçoit le modèle, et donc la suite de ses calculs.
- **Q114** (`image_only`) : la réponse est dans une image, qui n'est pas indexée. Avant, le modèle disait que les passages ne donnaient pas la date. Maintenant, il ajoute la phrase de refus, et la réponse compte comme un refus à tort. Le contenu est le même.
- **correctness** : seule la note de Q024 change, de 0,3 à 0,4, sur une réponse reformulée.
- **faithfulness** : la hausse de 0,056 vient de trois notes. Q002 passe de 0 à 1, Q116 de 0 à 1, et Q117 de 1 à 0,75. Les réponses de Q116 et Q117 sont identiques à celles de l'expérience 4. Q002 est la question de `decision_history` que le juge pénalise (voir la section 3) : selon les runs, elle a obtenu 0 (n° 1, 4, 6, 7) ou 1 (n° 2, 3, 9). Cette hausse relève du bruit du juge.
- **Pièges** : 13 réponses sur 17 sont identiques. Les 4 autres (Q008, Q026, Q096, Q099) ne donnent pas la valeur piège.

#### Décision : le prompt est conservé

Il ne change aucun résultat et ne coûte rien. Il rend explicite le comportement attendu face aux passages néerlandais et anglais, ce qui servirait avec un modèle moins discipliné. C'est la même logique que pour le stemmer de l'étape 1. La configuration n° 9 devient `v0.3-langues`.

### Bilan de la section 4

| | Référence `v0.2-baseline` (n° 1) | `v0.3-langues` (n° 9) |
|---|---|---|
| hit@5 | 0,787 | 0,787 |
| MRR | 0,708 | 0,708 |
| recall@5 | 0,762 | 0,762 |
| nDCG@5 | 0,697 | 0,697 |
| hit@5 / MRR `multilingual` (7) | 0,86 / 0,69 | 0,86 / 0,69 |
| Refus à tort | 17/122 (13,9 %) | 18/122 (14,8 %) |
| correctness (31) | 0,619 | 0,619 |
| faithfulness (31) | 0,871 | 0,927 |
| Réponses qui reprennent le piège | 1/17 (Q023) | 1/17 (Q023) |
| Temps de réponse moyen | 6,45 s | 6,35 s |

Par type de question, hit@5, MRR et taux de refus sont ceux de la référence. Il y a deux exceptions, qui portent chacune sur une seule question : le MRR de `excel_reasoning` (de 0,64 à 0,65, Q158) et les refus de `image_only` (de 0,69 à 0,77, Q114). Les correctness de `factual` (de 0,80 à 0,85) et de `scan_ocr` (de 0,35 à 0,30) changent chacune d'une note, sur 2 réponses jugées.

**La section n'améliore pas les résultats.** Elle explique en revanche pourquoi les questions `multilingual` résistent :

1. **La recherche lexicale n'est pas en cause.** La ligne de contexte, en français, apporte déjà les chunks néerlandais et anglais (section 3). Le stemmer de leur langue ne change rien.
2. **La traduction de la question retrouve le rapport de Q062 parmi les candidats, mais le reranker le recule.** Reranker chaque passage avec la question dans sa langue récupère Q062, mais fait perdre Q024 et Q112. Les traductions n'emploient pas les mots des documents, et les scores obtenus avec des questions différentes ne sont pas comparables entre eux.
3. **La génération répondait déjà en français** : la consigne explicite ne change rien.
4. **Le bruit de mesure est important.** Sans aucun changement de la recherche, la correctness varie d'environ 0,03 et la faithfulness jusqu'à 0,1 sur les 31 questions jugées. Le juge renvoie parfois un JSON invalide (Q008, Q002) : il faut vérifier qu'aucune note n'est vide avant de lire les moyennes.

**Ce qui reste à faire** : Q062 reste sans sa preuve dans `v0.3-langues`. Sa réponse est juste mais incomplète, et elle s'appuie sur un projet de PV. Deux pistes n'ont pas été testées : reranker chaque passage avec les trois versions de la question et garder le meilleur score (étape 3) ; compter la notice néerlandaise d'Aéris 9 comme preuve de Q117 dans le jeu d'évaluation.

## Section 5 : les fichiers Excel (`v0.4-excel`)

Le corpus contient 55 classeurs. L'inventaire en exclut 6 (3 doublons, 2 fichiers de données personnelles, 1 fichier sans intérêt) : 49 sont indexés. Jusqu'ici, Docling les convertissait en tableaux Markdown. Il écrit alors les pourcentages en décimal (`-0.00681316572305923`), recopie le titre fusionné dans chaque colonne et perd le nom de l'onglet.

Dans le jeu de développement, 21 questions ont une preuve dans un classeur : les 13 `excel_lookup`, les 5 `excel_reasoning`, les pièges du budget (Q043) et du tarif (Q089), et Q081. La section teste deux changements, ajoutés à `v0.3-langues` (n° 9) :

1. lire les classeurs avec openpyxl, une phrase par ligne de tableau (n° 10, retenu) ;
2. pour `excel_reasoning`, des fonctions de calcul que le LLM choisit (non réalisée).

### Étape 1 : lire les classeurs avec openpyxl (n° 10)

#### Le changement testé

`etl/excel.py` (repris du notebook, partie 2) ouvre chaque classeur avec openpyxl (`data_only=True`, pour lire les valeurs calculées et non les formules). Il découpe chaque onglet en blocs : titre, en-tête, lignes, notes. Les valeurs sont écrites comme Excel les affiche : un pourcentage au format `0.0%` devient `-0,7 %`. Les nombres gardent le rendu de Docling (`4568`, `41.5`), celui des extraits de preuve.

- **Tableau de 30 lignes ou moins** : une phrase par ligne, qui reprend le fichier, l'onglet, le titre du tableau, puis chaque valeur précédée du nom de sa colonne :
  ```
  Reporting 2026-03 · onglet « Ventes par région » · Chiffre d'affaires par région (k€) · Région : Flandre ; CA du mois : 4358 ; Part : 32,0 %
  ```
- **Tableau de plus de 30 lignes** (2 cas : le suivi du rappel Aéris 12, 214 lignes, et les réponses brutes de l'enquête sur le télétravail, 84 lignes) : un chunk de résumé (nombre de lignes, liste des colonnes), puis des paquets de 20 lignes en Markdown, avec l'en-tête répété.

La ligne de contexte du document précède chaque chunk, comme pour les autres formats. Le payload reçoit en plus l'onglet (`sheet`) et le numéro de la première ligne dans l'onglet (`row`). La période et la version y figuraient déjà. Pour la langue, chaque chunk reprend celle du classeur (40 en français, les 9 `Productierapport Gent` en néerlandais) : une phrase faite de noms de colonnes et de nombres se détecte mal.

Le réglage s'active dans le TOML (`[chunking] excel_reader = 'openpyxl'`) et ajoute le suffixe `_xlsx` au nom de la collection. L'index du n° 9 est donc conservé.

#### Deux corrections du code du notebook

Les 49 classeurs comptent 95 onglets, tous visibles. Aucune formule n'est sans valeur calculée (notebook, partie 2.2). Aucune date n'est stockée comme une date : elles sont toutes écrites en texte (`06/07/2026`). Les nombres se limitent à 902 entiers, 180 pourcentages et 155 décimaux sans format. Sur ce corpus, le découpage du notebook (`sheet_tables`) a deux défauts :

1. **Il prend toujours la première ligne d'un bloc pour un en-tête.** Trois blocs n'en ont pas :
   - l'onglet `Synthèse` de l'enquête (`Nombre de réponses | 84`, …, `Satisfaction moyenne | 8.1`) ;
   - l'onglet `Synthèse` du rappel (`Unités concernées | 214`) ;
   - la ligne 17 du plan de formation (`Heures de formation à la sécurité | 620`).

   Cette dernière ligne devenait l'en-tête d'un tableau vide et disparaissait, alors que c'est la preuve de Q113. Correction : un en-tête ne contient que du texte. Sinon, le bloc est lu ligne par ligne, sous la forme « libellé : valeur ».
2. **Il perd les onglets qui ne contiennent que des cellules isolées.** C'est le cas des 5 onglets `Commentaires` des reportings, par exemple : « Valtek prend en charge 65 % du coût du rappel (117 000 €) ». Leur texte restait en attente comme titre d'un tableau qui ne venait jamais. Correction : à la fin d'un onglet, un titre resté sans tableau devient un chunk de texte.

#### Vérification avant l'indexation

| | Docling (n° 9) | openpyxl (n° 10) |
|---|---|---|
| Chunks des classeurs | 111 | 551 |
| Chunks au total | 1 184 | 1 624 |
| Mots par chunk de classeur (moyenne / médiane / max) | 190 / 189 / 309 | 49 / 39 / 361 |
| Preuves Excel contenues dans un chunk | 23/26 | 23/26 |

Les chunks des autres formats sont identiques : même nombre pour chaque format. Les 23 preuves trouvées avec Docling le sont aussi avec openpyxl. Les 3 autres sont dans des documents non indexés : `Copie de Tarif 2026` et l'annexe de la grille ERP sont des doublons, et la `Grille salariale 2026` est dans `02_RH/Confidentiel`. Les passages pièges du budget et du tarif restent eux aussi dans un chunk. Le plafond de la recherche ne change donc pas : l'expérience mesure seulement l'effet de la forme des chunks.

Effet de bord : la longueur moyenne d'un chunk, que BM25 utilise pour tout le corpus, passe de 71 à 56 mots. Le classement BM25 des autres documents peut donc bouger un peu.

#### Comparabilité

Entre les commits `530973a` (n° 9) et `3b024a1` (n° 10), en dehors du rapport, de l'export CSV et du notebook, seuls ont changé la lecture des classeurs et son branchement dans le chunker, l'indexation et la recherche (nom de la collection), ainsi que le TOML. La génération, le reranker et le prompt sont les mêmes. Le top 5 change pour 58 questions : les chunks des classeurs ont changé, et la longueur moyenne utilisée par BM25 aussi.

#### Résultats (Docling → openpyxl)

| | Docling (n° 9) | openpyxl (n° 10) |
|---|---|---|
| hit@5 | 0,787 | 0,787 |
| MRR | 0,708 | 0,706 |
| recall@5 | 0,762 | 0,758 |
| nDCG@5 | 0,697 | 0,694 |
| `excel_lookup` (13) : hit@5 / MRR / refus | 0,92 / 0,85 / 0,08 | 0,92 / **0,88** / 0,08 |
| `excel_reasoning` (5) : hit@5 / MRR / recall@5 | 1,00 / 0,65 / 1,00 | 1,00 / 0,62 / 0,90 |
| `version_trap` (4) : hit@5 / MRR | 1,00 / 0,81 | 1,00 / 0,67 |
| Refus à tort | 18/122 (14,8 %) | 18/122 (14,8 %) |
| correctness (31) | 0,619 | 0,610 |
| faithfulness (31) | 0,927 | 0,839 |
| `trap_hit` | 7/17 | 7/17 |
| `trap_avoided` selon le juge | 15/17 (0,88) | 15/17 (0,88) |
| Réponses qui reprennent le piège, après relecture | 1/17 (Q023) | 1/17 (Q023) |
| Tokens envoyés au LLM par question (moyenne) | 1 915 | **1 688** |
| Temps de réponse moyen / médian / 90e centile | 6,35 s / 6,15 s / 10,6 s | **5,75 s / 5,08 s / 9,9 s** |
| Durée du run | 272 s | 247 s |

hit@5 ne change pour aucune question. Le MRR change pour 6 questions, et le taux de refus pour 2.

#### Les questions dont la preuve est dans un classeur

L'échantillon du juge ne contient que 2 questions par type. J'ai donc relu les réponses aux 21 questions des deux runs. Dans les deux, 20 réponses sont justes. Seule Q154 échoue : sa preuve est dans un document non indexé. Q081 reçoit une réponse juste (725 k€), mais tirée des PV de COPIL Atlas qui occupent le top 5, sans aucune preuve de grade 2. Les différences :

- **Q124** (montant de l'ERP dans le budget approuvé) : la preuve passe de la 2e à la 1re place, et la réponse précise maintenant « approuvé par le conseil d'administration le 16 décembre 2025 ».
- **Q043** (piège du budget) : les phrases des versions 1 et 2 du budget passent devant celle du budget approuvé, qui recule de la 1re à la 3e place. Les trois phrases ne diffèrent que par le nom du fichier, la ligne de contexte et le montant. La réponse reste juste (280 k€) et cite le budget approuvé.
- **Q126** (baisse du chiffre d'affaires budgété) : la ligne `Total 2026` de la version 1 sort du top 5 (recall@5 de 1 à 0,5). La réponse reste juste (−2,5 M€) grâce à la note de présentation du budget.
- **Q158** (unités du rappel introuvables) : la correctness passe de 1 à 0,6. Le modèle cite bien « Chauffage Lambert & Fils », mais écrit aussi que le document ne précise pas le nom de l'installateur : la réponse se contredit.
- **Q101** (`multi_doc`) : l'onglet `Commentaires` du reporting de mars, que le code du notebook aurait perdu, arrive 1er : « Valtek prend en charge 65 % du coût du rappel ». La preuve recule à la 2e place (MRR de 1 à 0,5), mais la réponse est la même et reste juste.

#### Deux effets de la forme des chunks

- **Les chunks de classeur s'invitent moins dans les autres questions.** Avec Docling, 29 questions sans preuve Excel avaient au moins un chunk de classeur dans leur top 5. Avec openpyxl, elles ne sont plus que 20. Un gros tableau de 190 mots ressemble à beaucoup de questions, une phrase de 39 mots à peu. Par exemple, le plan de formation et le budget sortent du top 5 de Q024 (`multilingual`), dont la preuve passe de la 2e à la 1re place.
- **Le top 5 se remplit de lignes d'un même classeur.** Avant, 15 questions avaient au moins 3 chunks du même document dans leur top 5. Elles sont maintenant 28. Q103 et Q121 en ont 5 sur 5. C'est sans conséquence pour une question sur une seule valeur. Mais pour une question qui demande aussi un document texte, la place peut manquer.

#### Les autres changements

- **Refus** : Q024 compte maintenant comme un refus. Elle donne le délai d'intervention, puis ajoute la phrase de refus pour le coût, qui manque. Q114, à l'inverse, n'en est plus un. Le nombre de refus à tort ne change pas.
- **faithfulness** : la baisse de 0,927 à 0,839 vient du bruit du juge. Pour Q082, Q098 et Q144, la réponse est identique à celle du n° 9, mais la note change (Q098 monte, les deux autres baissent). Q002 retrouve sa formulation du n° 4 et sa note de 0. La réponse de Q117 devient un refus.
- **Autres types** : le MRR de `multilingual` passe de 0,69 à 0,76 (Q024), celui de `multi_doc` baisse d'une question (Q101).
- **Pièges** : 13 réponses sur 17 sont identiques. Les 4 autres (Q008, Q043, Q089, Q091) ne donnent pas la valeur piège. Q089 cite le nom du produit, qui fait partie de l'extrait piège, mais donne le prix juste (18 110 €).

#### Coût

Les chunks sont plus courts : le prompt envoyé au LLM perd 12 % de tokens, et le temps de réponse moyen baisse de 0,6 s. L'index passe de 1 184 à 1 624 points.

#### Décision : la lecture par openpyxl est retenue

1. **Elle ne perd rien** : le plafond de la recherche est le même, hit@5 ne change pour aucune question, et les réponses aux questions Excel restent justes, sauf la réponse contradictoire de Q158.
2. **Elle corrige ce que Docling abîmait** : les pourcentages, le nom de l'onglet, le titre du tableau et l'unité sont dans chaque chunk, et les onglets de commentaires sont lus.
3. **Elle rend les chunks plus précis et moins coûteux** : moins de chunks de classeur dans les questions qui n'en ont pas besoin, 12 % de tokens en moins.
4. **Elle prépare l'étape 2**, qui a besoin des tableaux sous forme structurée.

Elle n'améliore pas les métriques. Les questions Excel du jeu de développement étaient déjà bien traitées par Docling (hit@5 de 0,92 et 1,00), parce que leurs extraits de preuve ne contiennent ni pourcentage ni date mise en forme. Les 5 questions `excel_reasoning` reçoivent déjà une réponse juste du RAG seul : l'étape 2 a donc peu de marge sur ce jeu.

### Étape 2 : des fonctions de calcul pour `excel_reasoning`

Non réalisée. Les 5 questions `excel_reasoning` du jeu de développement reçoivent déjà une réponse juste du RAG seul (étape 1), et la marge de l'étape était donc faible. Le temps est allé à la section 6 : 32 questions du jeu de développement ont une preuve dans une image ou un scan, que l'index ne contenait pas.

## Section 6 : les images et les scans (`v0.5-images`)

Le corpus contient 54 images et 9 PDF scannés, sans couche de texte. L'inventaire exclut un scan (`99_Archives/Divers/scan0001.pdf`, classé comme bruit) : il reste 8 scans, soit 9 pages. Jusqu'ici, la conversion et le chunking les écartaient tous (`source_type NOT IN ('image', 'scan')`).

Dans le jeu de développement, 32 questions ont une preuve dans l'un de ces documents :
- les 13 `image_only` ;
- les 6 `scan_ocr` ;
- 13 questions d'autres types (`decision_current`, `decision_history`, `decision_reason`, `board_resolution`, `multi_doc`…), dont la preuve est souvent un PV signé scanné.

Les 2 questions `image_in_document` ont leur preuve dans un graphique d'un PDF texte : Q045, qui est dans la réserve de test, et Q144. Elles relèvent d'une étape à part.

La section teste trois changements, ajoutés à `v0.4-excel` (n° 10) :

1. transcrire les images et les scans avec le VLM (n° 12, retenu) ;
2. sur les documents numérisés, comparer le VLM et l'OCR de Docling (n° 14, non retenu) ;
3. lire les graphiques des PDF texte (n° 15, retenu).

### Étape 1 : transcrire les images et les scans avec le VLM (n° 12)

#### La transcription

`etl/vision.py` envoie chaque image au service `llama-vision`, avec une température de 0. Le service fait tourner Qwen3.8-27B avec son projecteur d'images (`mmproj-F16`), 1 slot, un contexte de 8 192 tokens et le décodage spéculatif MTP. llama-swap le charge à la demande sur le port 8000, à la place de Qwen texte : le port 8003 de l'énoncé n'est pas utilisé.

- **Les images** sont réduites à 1 600 px de côté au plus et envoyées en JPEG.
- **Les pages des scans** sont rendues à 150 dpi avec PyMuPDF.
- **Le prompt** demande deux choses :
  - recopier tout le texte visible, exactement comme il est écrit (nombres, codes, dates, unités, annotations manuscrites), avec les tableaux en Markdown ;
  - puis, sous le titre « Description », décrire en trois phrases au plus le type d'image et ce qui n'est pas écrit : rattachements d'un organigramme, valeur la plus haute d'un graphique, position des éléments d'un plan.

  Un élément illisible doit être noté `[illisible]`.
- **La réponse** est limitée à 2 500 tokens. Une transcription coupée par cette limite reçoit la mention `[transcription tronquée]`. Aucune ne l'a reçue.

Chaque transcription est calculée une seule fois et gardée dans `data/vision/`, un fichier JSON par image ou par page. La clé combine l'empreinte SHA-256 du fichier, la page, le modèle et le prompt :
- un fichier renommé n'est pas relu ;
- un changement de prompt fait tout relire.

Le JSON garde aussi le temps de transcription, le modèle et le prompt. Comme les exports Docling, le cache n'est pas commité (`data/` est dans le `.gitignore`). Le README donne la commande qui le reconstruit.

#### Temps de lecture

| Documents | Transcriptions | Temps par transcription |
|---|---|---|
| Photos d'équipement | 10 | 4,5 à 5,8 s |
| Graphiques, tableaux de bord, schémas, plannings, plans | 19 | 4,7 à 9,4 s |
| Factures et bons de livraison | 18 | 6,2 à 10,5 s |
| Organigrammes | 4 | 8,1 à 10,3 s |
| Photos de tableaux blancs, affiche | 3 | 5,5 à 6,5 s |
| Scans d'une page (courriers, avenant, attestation) | 4 | 7,2 à 8,5 s |
| Pages de PV du conseil scannées | 5 | 15,3 à 16,6 s (5,2 s pour la page des signatures) |
| **Total** | **63** | **8,0 min** |

Une page de PV est longue : chaque première page donne plus de 512 tokens de transcription, d'où le temps plus long.

#### Vérification de dix transcriptions

J'ai comparé dix transcriptions à leur image, en prenant un type de document différent à chaque fois :

| # | Document | Type | Nombres, dates, codes | Noms |
|---|---|---|---|---|
| 1 | Organigramme direction 2026-04 | organigramme | justes | « Detthier » au lieu de « Dethier » |
| 2 | Facture Tôlerie Mosane TM-2025-0391 | facture | justes | « Aérís » au lieu de « Aéris » |
| 3 | PV CA 2025-11-18 signé, page 1 | scan | justes (montants, scores, absent excusé) | justes |
| 4 | Photo Heftruck nr 7 | photo d'une plaque | 7/7 | justes |
| 5 | Photo du tableau SWOT | tableau blanc manuscrit | justes (92 %, +20 %, 26/08/2025) | « Aérís » au lieu de « Aéris » |
| 6 | Plan de l'entrepôt de Gand | plan | justes (12 allées, 6 et 10 km/u, 14 chariots) | justes |
| 7 | Taux de réclamations 2025-2026 | graphique en courbe | 10/10 (9 points et l'objectif) | justes |
| 8 | Tableau de bord commercial 2026-03 | indicateurs et barres | 8/8 | justes |
| 9 | Bon de livraison Elcora | bon et note manuscrite | justes | justes (« R. Dethier » manuscrit bien lu) |
| 10 | Planning Atlas v2 | diagramme de Gantt | 17/17 (16 dates et le go-live) | justes |

**3 erreurs sur 10 transcriptions, toutes sur des noms propres.** Aucun des plus de 80 nombres, dates et codes vérifiés n'est faux. Chaque erreur porte sur un seul caractère :
- une lettre en trop : « Detthier » ;
- l'accent sur le mauvais « i » : « Aérís ».

Dans l'ensemble du cache, le nom de la gamme est écrit « Aérís » dans 3 des 9 transcriptions où il apparaît.

L'effet sur la recherche est faible :
- le BM25 plie les accents, donc « Aérís » et « Aéris » donnent le même terme ;
- seule l'erreur « Detthier » peut faire rater une recherche par mot-clé ;
- aucun extrait de preuve n'est touché (voir plus bas).

Les descriptions ont aussi des défauts, sans nombre ni nom faux :
- le tableau SWOT, une photo de tableau blanc, y devient une « diapositive » ;
- le bon Elcora y devient une « facture de livraison » ;
- le plan de Gand est forcé dans un tableau Markdown, qui ne rend les positions qu'en partie.

Corriger « Aéris » avec une liste de noms propres reviendrait à ajuster la chaîne au jeu d'évaluation. Je ne l'ai pas fait.

#### Les chunks

Le chunker (`chunk_transcription`) relit les transcriptions dans le cache et n'appelle pas le VLM. Chaque chunk contient trois éléments :
- la ligne de contexte du document ;
- une ligne d'en-tête : « Transcription de l'image « … » », ou « Transcription du scan « … », page 2 sur 2 » ;
- la transcription.

Une page qui tient dans 512 tokens forme un seul chunk. Sinon, les paragraphes sont regroupés jusqu'à 512 tokens. Un tableau Markdown n'est jamais coupé, et les lignes de séparation du VLM (`***`, `---`) sont retirées.

Le payload reçoit en plus `image_path` et `page` (à partir de 0, ou `None` pour une image), pour pouvoir afficher l'image sous la réponse. La langue est détectée sur chaque chunk.

Le réglage s'active dans le TOML (`[corpus] include_images` et `include_scanned_pdfs`). Il ajoute les suffixes `_img` et `_scan` au nom de la collection, ce qui conserve l'index du n° 10.

#### Vérification avant l'indexation

| | n° 10 | n° 12 |
|---|---|---|
| Points dans l'index | 1 624 | 1 695 (+71) |
| Chunks d'images et de scans (62 documents) | – | 71 |
| Tokens par chunk de transcription (moyenne / max) | – | 321 / 512 |
| Preuves contenues dans un chunk de transcription | – | 36/36 |

8 documents sont découpés en 2 ou 3 chunks : les 4 PV scannés et les 4 organigrammes. Pour un organigramme, le premier chunk contient le tableau entier, avec tous les noms, et le second ne contient que la description.

Les 36 preuves des 32 questions sont chacune dans un chunk de leur document, y compris celles qui citent un nom mal transcrit ailleurs.

Les scans font aussi entrer des pièges. Quatre questions du jeu de développement ont leur passage piège dans une transcription :
- Q023, Q081 et Q096, dans les PV du conseil scannés du 18/11 et du 16/12 ;
- Q056, dans l'organigramme de septembre 2025.

#### Comparabilité

Entre les commits `3b024a1` (n° 10) et `4546dab` (n° 12), en dehors du rapport, de l'export CSV et du notebook, ont changé :
- `etl/vision.py`, qui est nouveau ;
- la configuration (`vision_model`, `vision_folder`) ;
- la liste des documents à transcrire dans `db.py` ;
- le chunking des transcriptions ;
- le nom de la collection dans l'indexation et la recherche ;
- le TOML et le README.

La génération, le reranker et le prompt sont les mêmes. Le top 5 change pour 51 questions.

Le n° 11 tourne sur le même commit. Son juge s'est arrêté après 10 notes, mais ses 127 réponses sont complètes : 110 sont identiques à celles du n° 12. C'est l'ordre de grandeur du bruit de la génération, à code égal.

#### Résultats (n° 10 → n° 12)

| | n° 10 | n° 12 |
|---|---|---|
| hit@5 | 0,787 | **0,934** |
| MRR | 0,706 | **0,839** |
| recall@5 | 0,758 | **0,910** |
| nDCG@5 | 0,694 | **0,831** |
| Refus à tort | 18/122 (14,8 %) | **5/122 (4,1 %)** |
| correctness (31) | 0,610 | **0,745** |
| faithfulness (31) | 0,839 | 0,903 |
| `trap_hit` | 7/17 | 7/17 |
| `trap_avoided` selon le juge | 15/17 (0,88) | 15/17 (0,88) |
| Réponses qui reprennent le piège, après relecture | 1/17 (Q023) | **0/17** |
| Tokens envoyés au LLM par question (moyenne) | 1 688 | 1 808 |
| Temps de réponse moyen / médian / 90e centile | 5,75 s / 5,08 s / 9,9 s | 6,20 s / 5,58 s / 10,0 s |
| Durée du run | 247 s | 267 s |

| Type (questions) | hit@5 | MRR | Refus | correctness (2 jugées) |
|---|---|---|---|---|
| `image_only` (13) | 0 → **0,85** | 0 → **0,85** | 69 % → **8 %** | 0 → **0,80** |
| `scan_ocr` (6) | 0,17 → **1,00** | 0,17 → **1,00** | 67 % → **0 %** | 0,35 → **0,75** |
| `board_resolution` (6) | 0,83 → **1,00** | 0,71 → 0,83 | 0 % → 0 % | 0,60 → **1,00** |
| `multi_doc` (5) | 1,00 → 1,00 | 0,90 → 0,90 | 20 % → **0 %** | 0,50 → **1,00** |
| `decision_current` (14) | 0,79 → 0,86 | 0,67 → 0,70 | 0 % → 0 % | 0,60 → 0,60 |
| `image_in_document` (1) | 0 → 0 | 0 → 0 | 100 % → 100 % | 0 → 0 |

Aucune question ne perd sa preuve. **18 questions la trouvent maintenant** :
- 11 `image_only` ;
- les 5 `scan_ocr` qui la manquaient ;
- Q049 (`board_resolution`) et Q133 (`decision_current`), qui ont une preuve dans un PV signé scanné ou un organigramme.

#### Les questions gagnées

Quelques exemples :

- **Q098** (« Quel a été le taux de réclamations clients en décembre 2025 ? ») : le refus devient « 1,9 % », lu sur le graphique.
- **Q107** (première cause de non-conformité en 2025) : la réponse fausse du n° 10, tirée d'une fiche de non-conformité, devient « le fournisseur, avec 19 fiches », lu sur le Pareto.
- **Q038** (IBAN de la facture TM-2026-0042) : le n° 10 citait l'IBAN frauduleux de l'incident de paiement. Le n° 12 lit le bon IBAN sur la facture (BE47 0689 4412 7380).
- **Q117** (`multi_doc`, niveau sonore de l'Aéris 9) : le refus devient la bonne réponse. Les 58 dB(A) viennent du courrier scanné d'Habitat Confort, les 52 dB(A) de la fiche technique.
- **Q023** (montant approuvé pour la phase 1 de la ligne L4) : le n° 10 reprenait le piège (1,2 M€). Le scan du PV du 16 décembre 2025 contient la correction (« 1 250 000 et non de 1,2 »), et la réponse devient juste : 1 250 000 €, en signalant la correction.

#### Les deux échecs `image_only` : les organigrammes

Q056 (« À qui le service des achats est-il rattaché depuis avril 2026 ? ») et Q147 (« Qui est responsable du service après-vente ? ») ont leur preuve dans les organigrammes. J'ai relancé la recherche sur ces deux questions : **le chunk qui contient le tableau n'entre jamais dans les 30 candidats**, pour aucun des 4 organigrammes. Seuls les chunks de description remontent.

- Pour Q147, aucun chunk d'organigramme n'est candidat, et la réponse est un refus.
- Pour Q056, la description de l'organigramme d'avril 2026 arrive 3e : « la CEO, Hélène Marchal, supervise directement six directions ». Le LLM répond donc « Hélène Marchal », alors que la bonne réponse est Thomas Lambert. Ce n'est pas la valeur du piège (Laurent Dewit).

Dans le tableau, les services d'un directeur sont rangés dans sa colonne, et chaque ligne mélange six directions (`Achats<br>Céline Moreau` est sous `Thomas Lambert`, quatre lignes plus bas). Le chunk de 495 tokens est trop long et trop dilué pour la recherche dense, le BM25 et le reranker.

Piste, dans l'esprit de la lecture des classeurs en section 5 : une phrase par service, par exemple « Achats : Céline Moreau, rattachée à Thomas Lambert, directeur des opérations ». On peut l'obtenir de deux façons :
- avec un prompt propre aux organigrammes (4 images à relire) ;
- avec du code qui relit le tableau colonne par colonne.

#### Les autres changements

- **Les chunks d'images et de scans s'invitent dans d'autres questions.** 19 questions sans preuve dans une image ou un scan en ont au moins un dans leur top 5 (78 places sur 635 au total). Pour trois questions, la preuve recule d'un rang ou plus, sans sortir du top 5 :
  - Q003 : 4 PV scannés dans le top 5 ; la réponse reste juste ;
  - Q052 : le planning L4 au 1er rang ;
  - Q086 : la note de crédit Valtek au 3e rang.

  Les 5 questions `out_of_corpus` restent refusées, même les 3 qui reçoivent un chunk de transcription.
- **Refus** : il reste 5 refus à tort, qui l'étaient déjà au n° 10 : Q024, Q093, Q154, Q144 (le graphique d'un PDF texte) et Q147 (l'organigramme ci-dessus).
- **correctness** : 9 notes sur 31 changent.
  - Hausses : Q023 (0,2 → 1), Q038 (0 → 0,8), Q098 (0 → 0,7), Q107 (0 → 0,9), Q117 (0 → 1), Q058 (0,8 → 1) et Q052 (0,6 → 0,7).
  - Baisses : Q013 (1 → 0,9), dont le top 5 reçoit le PV scanné du 18/11, et Q158 (0,6 → 0,4), dont la réponse change avec le même top 5. C'est le niveau habituel du bruit de génération.
- **Pièges** : `trap_hit` reste à 7/17.
  - Q023 était déjà touchée par le projet de PV en docx.
  - Pour Q056, Q081 et Q096, le chunk piège du scan n'entre pas dans le top 5.
  - Aucune réponse ne reprend la valeur piège. Q008 reste incomplète, comme avant, sans donner la valeur piège. Q056 est fausse pour une autre raison.

#### Coût

- **À l'indexation** : 8,0 min de transcription, une seule fois, puis 71 points de plus dans l'index.
- **À chaque question** : 7 % de tokens en plus dans le prompt (1 688 → 1 808), et 0,45 s de plus en moyenne (5,75 → 6,20 s). Le 90e centile ne bouge presque pas.

#### Décision : la transcription par le VLM est retenue

1. **C'est le plus gros gain du projet** : hit@5 de 0,787 à 0,934, refus à tort de 14,8 % à 4,1 %, correctness de 0,61 à 0,75. Aucune question ne perd sa preuve.
2. **Les transcriptions sont fiables sur les nombres** : aucun nombre faux sur les dix vérifiées, et 3 erreurs d'un caractère sur des noms.
3. **Le coût est faible** : 8 minutes une seule fois, et moins d'une demi-seconde par question.

Restent :
- les organigrammes, que la forme de leur tableau rend introuvables (Q056, Q147) ;
- les graphiques des PDF texte (Q144) ;
- les pièges des scans, qui ne remontent pas encore mais sont maintenant dans l'index, pour la section 7.

### Étape 2 : comparer le VLM et l'OCR de Docling sur les documents numérisés (n° 14)

#### Le changement testé

Les documents numérisés sont lus par l'OCR de Docling au lieu du VLM. Les 36 autres images restent transcrites par le VLM : organigrammes, graphiques, plans, schémas, photos d'équipement. Un OCR ne sait pas les décrire. Le n° 14 ne diffère donc du n° 12 que par la lecture des documents numérisés.

**Le périmètre.** Les 8 PDF scannés ne suffisent pas : seules 2 des 6 questions `scan_ocr` du jeu de développement (Q057, Q157) y ont leur preuve. Les 4 autres l'ont dans des photos JPG de factures ou de bons de livraison :
- Q038 : facture Tôlerie Mosane TM-2026-0042 ;
- Q042 : BL Kompra ;
- Q064 : BL Elcora ;
- Q119 : BL Valtek.

Le périmètre comprend donc 26 documents, soit 27 pages :
- les 8 PDF scannés ;
- les 12 factures et les 6 bons de livraison (`doc_type` `facture` et `bon_de_livraison` dans le registre).

**La conversion** (`etl/convert.py`, commande `scans`) :
- Docling avec `do_ocr = True` et le moteur RapidOCR, le seul installé (modèles PP-OCRv6 dans `models/docling/RapidOcr`) ;
- `force_full_page_ocr = True`, puisqu'un scan n'a pas de couche de texte. Sans OCR, Docling ne trouve aucun texte dans un scan : 3 emplacements d'image vides pour le PV du 18/11 ;
- les photos passent par le même pipeline (`InputFormat.IMAGE`) ;
- le modèle de mise en page tourne sur le GPU. RapidOCR tourne sur le CPU, car le paquet `onnxruntime` installé n'a pas de support CUDA ;
- le temps de chaque fichier est enregistré dans la table `document`, comme pour toutes les conversions.

**Le chunking.** Les exports passent par le chunker de Docling (`chunk_document`), comme les autres PDF. Le réglage s'active dans le TOML (`[corpus] scan_reader = 'docling'`, absent = VLM). Il ajoute le suffixe `_ocr` au nom de la collection. Si les documents ne sont pas encore convertis, l'indexation lance la conversion.

#### Comparaison des deux lectures avant l'indexation

| | OCR Docling | VLM |
|---|---|---|
| Temps de lecture : 8 PDF scannés (9 pages) | 21,5 s | 98,9 s |
| Temps de lecture : 18 photos de factures et de BL | 43,8 s | 142,7 s |
| Temps de lecture : total (26 documents) | **65,3 s** | 241,6 s |
| Chunks | 56 | 31 |
| Preuves et pièges du jeu de développement contenus dans un chunk | 13/15 | 15/15 |

Les temps de l'OCR comprennent environ 6 s de chargement des modèles au premier fichier de chaque lancement (8,0 et 7,7 s, contre 1,3 à 3,1 s pour les autres).

**Les PDF scannés imprimés (PV, courriers, avenant, attestation) : les deux lectures se valent.**
- Les mêmes nombres sont lus, et les 10 preuves et pièges sont trouvés par les deux.
- L'OCR fait quelques fautes sans conséquence (« 14 100 ke » pour « k€ », « DSl » pour « DSI »). Il écrit en revanche « Aéris » correctement, là où le VLM écrit « Aérís ».
- Il perd le pied de page, les signatures et la description, rien d'utile pour répondre.
- Il garde les titres de section, que le chunker de Docling utilise : 7 chunks par PV au lieu de 2, chacun précédé de son titre.

**Les photos de factures et de bons de livraison : le VLM lit mieux.** L'OCR a quatre défauts.

1. **Les lignes de bas de page disparaissent.** Docling classe la ligne de paiement en pied de page, que ni l'export Markdown ni le chunker ne gardent. L'OCR lit 8 des 9 IBAN des factures (celui d'Elcora devient « Bet g 2. »), mais aucun n'arrive dans un chunk. C'est le cas de la preuve de Q038.
2. **Certains en-têtes disparaissent aussi.** Le nom du fournisseur est parfois rangé avec le logo dans une zone traitée comme une image. « Kompra GmbH », « Pakmatic NV » et deux fois « Linetech Automation BV » ne sont dans aucun chunk.
3. **La structure est abîmée.**
   - Les blocs « libellé : valeur » sont défaits : `Date KG-DN-26-0388`, puis `03/03/2026` deux lignes plus bas.
   - Les cellules fusionnées sont dupliquées. La facture TM-2025-0391 donne ainsi 348 mots et 3 chunks, contre 190 mots et 1 chunk avec le VLM.
4. **Il y a des fautes de lecture.**
   - Un chiffre faux : quantité « 6 » au lieu de 9 sur TM-2025-0391 (9 × 2 760 = 24 840).
   - « 1ot » au lieu de « lot ».
   - « abimés » au lieu de « abîmés » dans la note manuscrite de Q064. L'extrait attendu ne correspond plus exactement.

   Les notes manuscrites sont lues, noms compris (« R. Dethier », « F. Collin »).

Le VLM n'est pas parfait non plus. La comparaison a fait apparaître deux erreurs de nom hors des dix transcriptions vérifiées à l'étape 1 : « Linotech » et « Linetechn » au lieu de « Linetech », vérifiées sur les images.

#### Comparabilité

Entre les commits `4546dab` (n° 12) et `1d0d1da` (n° 14), en dehors du rapport et de l'export CSV, ont changé :
- la conversion (option OCR, images acceptées) ;
- la liste des documents numérisés dans `db.py` ;
- le choix du lecteur dans le chunker ;
- l'appel de la conversion dans l'indexation ;
- le nom de la collection ;
- le TOML par défaut dans `config.py`, et le nouveau TOML.

La recherche, le reranker, la génération et le prompt sont les mêmes. L'index compte 1 720 points : les 1 695 du n° 12, moins les 31 chunks VLM des 26 documents, plus les 56 chunks OCR. Le top 5 change pour 39 questions, et 89 réponses sur 127 sont identiques.

**Un défaut découvert après le run, à l'étape 3.** Le commit `b90f2e8` avait laissé l'ancienne ligne de la boucle des images devant le nouveau choix entre OCR et VLM : chaque image passait deux fois par le chunker. Le contenu de l'index n'en souffre pas. Les doublons ont le même identifiant, et Qdrant garde le dernier point : les chunks OCR, produits après ceux du VLM et au moins aussi nombreux pour chacun des 26 documents, les ont tous remplacés.

En revanche, la longueur moyenne des chunks utilisée par le BM25 (`avg_len`) est calculée sur tout ce que produit le chunker, doublons compris. Elle valait 62 mots au lieu de 58. La normalisation du BM25 du n° 14 diffère donc un peu de celle qu'il aurait dû avoir.

Ce défaut ne touche pas les deux échecs `scan_ocr`, qui viennent du contenu des chunks : l'IBAN absent, et « abimés » au lieu de « abîmés ». Il peut en revanche expliquer une partie des petits déplacements de rang décrits plus bas. Le n° 14 n'a pas été relancé, parce que la décision n'en dépend pas. Le défaut est corrigé dans `cb648e0`, avant le n° 15.

#### Résultats (VLM → OCR Docling)

| | VLM (n° 12) | OCR Docling (n° 14) |
|---|---|---|
| hit@5 | 0,934 | 0,918 |
| MRR | 0,839 | 0,818 |
| recall@5 | 0,910 | 0,898 |
| nDCG@5 | 0,831 | 0,814 |
| `scan_ocr` (6) : hit@5 / MRR | 1,00 / 1,00 | **0,67 / 0,58** |
| `scan_ocr` (2 jugées) : correctness | 0,75 | **0,30** |
| Refus à tort | 5/122 (4,1 %) | 5/122 (4,1 %) |
| correctness (31) | 0,745 | 0,729 |
| faithfulness (31) | 0,903 | 0,903 |
| `trap_hit` | 7/17 | 8/17 |
| `trap_avoided` selon le juge | 15/17 (0,88) | 15/17 (0,88) |
| Réponses qui reprennent le piège, après relecture | 0/17 | 0/17 |
| Tokens envoyés au LLM par question (moyenne) | 1 808 | 1 714 |
| Temps de réponse moyen / médian / 90e centile | 6,20 s / 5,58 s / 10,0 s | 5,76 s / 5,28 s / 9,6 s |
| Temps de lecture des images et des scans | 8,0 min | **5,0 min** (VLM 236,8 s + OCR 65,3 s) |
| Durée du run | 267 s | 248 s |

hit@5 ne change que pour deux questions, Q038 et Q064, toutes deux `scan_ocr`. `image_only`, `multi_doc`, `board_resolution` et `decision_history` gardent le même hit@5.

#### Les questions `scan_ocr`, relues

| Question | VLM (n° 12) | OCR Docling (n° 14) |
|---|---|---|
| **Q038** (IBAN de la facture TM-2026-0042) | juste | **fausse** : la facture arrive 4e, mais sans sa ligne de paiement. La réponse dit que les passages « ne mentionnent pas l'IBAN légitime » et cite **l'IBAN frauduleux** du rapport d'incident (correctness de 0,8 à 0). |
| Q064 (note du réceptionnaire Elcora) | juste | juste, sans le nom de R. Dethier. hit@5 passe à 0 à cause de « abimés » : l'extrait attendu ne correspond plus exactement. |
| Q042 (palettes manquantes chez Kompra) | juste | juste (0,7 → 0,6 selon le juge, pour une réponse équivalente) |
| Q119 (réception du lot V-2544) | juste | juste (le bon de livraison passe du 1er au 2e rang) |
| Q057, Q157 (PDF scannés) | justes | réponses identiques |

Après relecture, le VLM a 6 réponses justes sur 6, et l'OCR 5 sur 6. La seule erreur est grave : à une question sur un IBAN, la réponse donne celui de l'escroquerie.

#### Les autres changements

- **Pièges** : le piège de Q096 (« geler les recrutements », PV scanné du 16/12) entre dans le top 5. Le chunk OCR, plus court et précédé de son titre de section, remonte mieux. La réponse reste juste et ne reprend pas le piège.
- **Rangs** : avec des chunks de PV plus courts, plusieurs preuves se déplacent d'un rang, sans sortir du top 5.
  - Q003 et Q086 montent.
  - Q023, Q096, Q119 et Q134 descendent.
  - Q101 retrouve ses deux preuves (recall@5 de 0,5 à 1).
- **Juge** :
  - Q116 (`out_of_corpus`) perd sa note de faithfulness (de 1 à 0), pour une réponse identique au n° 12. C'est le bruit du juge.
  - Q002, Q013 et Q158 changent de note, mais leur réponse a changé : c'est le bruit de la génération.

#### Coût

- **À la lecture** : l'OCR lit les 26 documents en 65 s au lieu de 242 s. Le temps de lecture des images et des scans passe de 8,0 à 5,0 min, une seule fois.
- **À chaque question** : sans description, les chunks sont plus courts. Le prompt perd 5 % de tokens, et chaque réponse 0,4 s.

#### Décision : le VLM reste le lecteur des documents numérisés

1. **Sur les photos de documents, le VLM lit mieux.** Il garde les pieds et les en-têtes de page, les paires « libellé : valeur » et tous les chiffres. L'OCR perd les IBAN et les noms de fournisseurs, et lit un chiffre de travers.
2. **La perte se voit dans les réponses** : `scan_ocr` passe de 6 à 5 réponses justes sur 6. Et la réponse fausse est dangereuse, puisqu'elle cite l'IBAN frauduleux.
3. **Le gain de l'OCR est faible** : 3 minutes une seule fois, et 0,4 s par question.

Garder l'OCR seulement pour les 8 PDF scannés, où il vaut le VLM, ferait gagner environ 80 s une seule fois, pour une chaîne plus compliquée. Je ne l'ai pas fait.

Une piste n'a pas été testée : faire garder par le chunker les pieds de page de Docling. Elle rendrait les IBAN, mais ni les en-têtes perdus, ni la structure, ni le chiffre faux.

### Étape 3 : les graphiques des PDF texte (n° 15)

#### Le changement testé

Les PDF texte peuvent contenir des graphiques dont les valeurs ne sont pas dans le texte. Seule la légende y est : « Figure : déchets industriels 2025 par filière ». Sur les 75 PDF texte indexés, PyMuPDF ne trouve que 3 images, et ce sont 3 graphiques de 1 320 × 715 px. Les exports Docling en comptent autant.

| Document | Graphique | Question |
|---|---|---|
| `Rapport RSE 2025.pdf` | déchets industriels 2025 par filière | Q144 (jeu de développement) : « 612 tonnes » |
| `2026-04-13 Annexe - Resultats enquete teletravail.pdf` | jour de présence commun souhaité | Q045 (réserve de test) : « mardi, 46 % » |
| idem | satisfaction, nombre de réponses par note | – |

`etl/vision.py` extrait ces images avec PyMuPDF (`page.get_images()`, en ne gardant que celles d'au moins 200 px de côté) et les transcrit avec le même VLM, le même prompt et le même cache. La clé du cache inclut en plus le numéro de l'image sur la page, puisque l'annexe en a deux sur la même page. Les clés existantes ne changent pas, et les 63 transcriptions déjà faites restent valables.

Chaque graphique donne un chunk, qui contient trois éléments :
- la ligne de contexte du document ;
- une ligne d'en-tête : « Graphique du document « Rapport RSE 2025 », page 1 » ;
- la transcription.

Ces chunks sont numérotés après les chunks Docling du même PDF. L'identifiant d'un point est calculé à partir du document et du numéro de chunk : repartir de 0 aurait écrasé des chunks du texte. Le payload garde `image_path` et `page`, pour pouvoir afficher la page sous la réponse.

Le réglage s'active dans le TOML (`[corpus] include_pdf_images = true`). Il ajoute le suffixe `_pdfimg` au nom de la collection.

#### Vérification des trois transcriptions

| Graphique | Valeurs | Structure |
|---|---|---|
| Jour de présence | 5/5 justes (mardi 46 %, jeudi 31 %…) | tableau jour → % juste |
| Satisfaction | 7/7 justes (note 8 : 32 réponses…), et « 84 réponses » | tableau note → nombre juste |
| Déchets par filière (RSE) | 5/5 nombres justes (612, 288, 74, 31, 156 t) | **tableau faux** |

Les deux graphiques de l'annexe concordent aussi avec le texte du PDF : 100 % pour les jours, 84 réponses, et une moyenne recalculée de 8,1.

Pour le graphique RSE, le VLM a recopié l'axe vertical au lieu d'associer chaque valeur à sa filière : « 612 t » est sur la ligne « 600 », « 74 t | 156 t » sur la ligne « 100 ». Seule la description donne deux paires : « Métaux » avec 612 tonnes, et « DEEE » avec 31. Ça suffit pour Q144. Mais une question sur les cartons ou les plastiques serait risquée.

Je n'ai pas relancé ce graphique avec un prompt propre aux graphiques : une seule question du jeu de développement en dépend. Les graphiques en images seules (taux de réclamations, tableaux de bord) avaient pourtant été bien transcrits à l'étape 1.

Les 3 transcriptions ont pris 23,2 s, dont sans doute environ 7 s de chargement du VLM par llama-swap au premier appel. Le temps total de lecture des images, des scans et des graphiques passe à **8,4 min**.

#### Un défaut du chunker, corrigé avant l'indexation

En vérifiant le chunker, j'ai trouvé le défaut décrit à l'étape 2 : chaque image passait deux fois par le chunker. Avec la config du n° 12, il produisait 1 766 chunks pour 1 695 points, et le BM25 aurait utilisé une longueur moyenne de 64 mots au lieu de 60. Sans correction, le n° 15 aurait donc mélangé deux changements.

Après la correction (`cb648e0`), le chunker produit pour exp08 exactement 1 695 chunks, sans doublon, avec un `avg_len` de 60 : c'est l'état du n° 12. La correction écarte aussi les scans quand `include_scanned_pdfs` vaut `false`, ce que l'ancienne version ne faisait pas.

#### Vérification avant l'indexation

| | n° 12 | n° 15 |
|---|---|---|
| Points dans l'index | 1 695 | 1 698 (+3) |
| Chunks produits / doublons | 1 695 / 0 | 1 698 / 0 |
| `avg_len` du BM25 | 60 | 60 |
| Tokens par chunk de graphique | – | 239 à 265 |
| Preuve de Q144 (« Métaux », « 612 ») dans un chunk | non | oui |
| Preuve de Q045 (« Mardi », « 46 ») dans un chunk | non | oui |

#### Comparabilité

Entre les commits `4546dab` (n° 12) et `33e9482` (n° 15), ont changé :
- le code de l'étape 2 (l'OCR, inactif dans cette config) ;
- l'extraction des images des PDF et la clé du cache dans `vision.py` ;
- le chunk des graphiques et la correction des doublons dans le chunker ;
- le nom de la collection ;
- le TOML.

La recherche, le reranker, la génération et le prompt sont les mêmes. Le top 5 change pour 4 questions : Q144, et Q033, Q047 et Q117, où seul l'ordre change, sans effet sur aucune métrique. Les 3 chunks de plus modifient légèrement l'IDF du BM25. 109 réponses sur 127 sont identiques.

#### Résultats (n° 12 → n° 15)

| | n° 12 | n° 15 |
|---|---|---|
| hit@5 | 0,934 | **0,943** |
| MRR | 0,839 | 0,847 |
| recall@5 | 0,910 | 0,918 |
| nDCG@5 | 0,831 | 0,839 |
| `image_in_document` (Q144) : hit@5 / refus | 0 / 1 | **1 / 0** |
| Refus à tort | 5/122 (4,1 %) | **4/122 (3,3 %)** |
| correctness (31) | 0,745 | **0,784** |
| faithfulness (31) | 0,903 | 0,968 |
| `trap_hit` | 7/17 | 7/17 |
| `trap_avoided` selon le juge | 15/17 (0,88) | 15/17 (0,88) |
| Réponses qui reprennent le piège, après relecture | 0/17 | 0/17 |
| Tokens envoyés au LLM par question (moyenne) | 1 808 | 1 806 |
| Temps de réponse moyen / médian / 90e centile | 6,20 s / 5,58 s / 10,0 s | 6,19 s / 5,48 s / 9,8 s |
| Durée du run | 267 s | 266 s |

- **Q144** : le refus devient « Calorvia a produit 612 tonnes de déchets métalliques en 2025 ». Le chunk du graphique arrive 1er. Le juge note 1 en correctness comme en faithfulness.
- **Aucun effet de bord** : le chunk d'un graphique n'entre dans le top 5 d'aucune autre question.
- **Le juge** :
  - Q158 passe de 0,4 à 0,6 en correctness, avec une réponse qui a changé (bruit de génération).
  - Gemma a de nouveau renvoyé un JSON invalide pour la faithfulness de Q002. La note, rejugée seule, vaut 1. La réponse a changé (« … jusqu'à l'arrivée d'un nouveau directeur financier »), et la note de Q002 alterne entre 0 et 1 d'un run à l'autre depuis la section 4.

  Sans Q002, l'effet propre de l'étape sur la faithfulness est d'environ +0,03, soit Q144 seule.

#### Coût

- **À l'indexation** : 3 transcriptions (23 s, une seule fois) et 3 points de plus dans l'index.
- **À chaque question** : rien ne change, ni les tokens ni le temps de réponse.

#### Décision : la lecture des graphiques des PDF est retenue

1. **Elle résout la seule question `image_in_document` du jeu de développement**, sans effet sur les autres questions. Elle prépare aussi Q045 pour l'évaluation finale.
2. **Elle ne coûte presque rien** : 23 s une seule fois, et rien par question.

Le n° 15 devient la meilleure configuration : hit@5 de 0,943, 4 refus à tort sur 122, correctness de 0,78.

Reste à faire : le tableau mal construit du graphique RSE.

## Section 7 : le temps et les versions (`v0.6-versions`)

Le corpus contient souvent plusieurs versions d'une même information, et la bonne réponse est la plus récente ou la seule officielle. On y trouve :
- un projet de PV et sa version signée ;
- un PV corrigé à la séance suivante ;
- un budget en v1, en v2, puis approuvé ;
- une décision prise, suivie, puis levée.

Les 17 questions avec piège listent les passages qui donnent une valeur périmée ou non officielle.

**Le point de départ est le n° 15**, la meilleure configuration de la section 6 :

| Type (questions du jeu de développement) | hit@5 | MRR | correctness (2 jugées) | Piège dans le top 5 |
|---|---|---|---|---|
| `decision_current` (14) | 0,86 | 0,70 | 0,60 | 1/10 |
| `decision_history` (6) | 1,00 | 0,92 | 0,75 | – |
| `board_resolution` (6) | 1,00 | 0,83 | 1,00 | 3/3 |
| `version_trap` (4) | 1,00 | 0,67 | 0,65 | 3/3 |
| `action_tracking` (11) | 1,00 | 1,00 | 0,55 | – |

**Le taux de pièges avant la section 7** :
- `trap_hit` = **7/17** : un passage piège est dans le top 5 pour Q023, Q026, Q027, Q043, Q048, Q089 et Q153.
- Après relecture, **0/17** réponse reprend la valeur piège. C'était 1/17 à la section 3 (Q023), avant que le PV correctif scanné du 16/12 soit indexé à la section 6.

La recherche trouve donc presque toujours la bonne preuve, mais le mauvais passage arrive avec elle. Le juge ne note que 2 questions par type : à chaque étape, les réponses aux questions avec piège sont relues.

La section teste les pistes du TODO une par une, de la moins chère à la plus chère, à partir du n° 15 :

1. un filtre `must_not` sur le statut du registre (n° 16, retenu) ;
2. des consignes de lecture dans le prompt (n° 17, retenu) ;
3. plus de passages après le reranking, à la place de « plus de candidats avant le reranking » (à venir).

### Étape 1 : écarter les projets avec un filtre `must_not` sur `status` (n° 16)

#### Le changement testé

Le registre donne à chaque document un statut, tiré de son nom et de son dossier (`version_status`, section 1) : `projet`, `valide`, `archive`, `copie`, `modele` ou rien. Ce statut est recopié dans le payload de chaque chunk, et Qdrant l'indexe déjà.

La recherche reçoit un filtre `must_not` sur `status ∈ ['projet']`, réglé dans le TOML (`[search] exclude_status`). Il s'applique avant le reranking. La recherche hybride renvoie toujours 30 candidats.

Les 4 documents écartés sont :
- les 3 projets de PV du CA (18/11/2025, 17/02/2026 v1, 19/05/2026) ;
- le projet de tarif 2026 v1.

Les autres statuts ne sont pas filtrés :
- **les archives** : la preuve de Q092 (`decision_history`, la limite de vitesse d'avant l'accident) est un PV de CODIR de 2024 rangé dans `99_Archives` ;
- **les copies** : elles sont déjà exclues de l'index par l'inventaire (`duplicate_content`) ;
- **les modèles** : le registre n'en contient aucun.

Aucune preuve du jeu de développement n'est dans un document `projet`.

#### Une correction du registre

En préparant le filtre, j'ai comparé le statut enregistré dans le registre à la règle actuelle de `version_status`, pour les 393 documents. Un seul diffère : `Le projet Atlas en 10 questions.html`, une FAQ de l'intranet, était enregistré `projet` alors que la règle lui donne `None`. Le filtre l'aurait écartée à tort.

Le registre a été corrigé par un `UPDATE`, puis l'index reconstruit. Le filtre ne joue qu'à la recherche, donc la collection garde le nom de celle du n° 15. Pour le n° 15, rien ne change : sans filtre, le statut ne sert pas.

#### Vérification avant le run

- Sur l'index du n° 15, la recherche hybride renvoie 30 candidats avec le filtre, dont 0 projet. Sans le filtre, elle en renvoyait 3 à 5 pour Q023, Q026, Q027 et Q089.
- L'index reconstruit compte 1 698 points, dont 32 chunks `projet` (les 4 documents). La FAQ Atlas n'a plus de statut.

#### Comparabilité

Entre les commits `33e9482` (n° 15) et `6010c97` (n° 16), seuls ont changé :
- le filtre dans `search.py` ;
- le TOML ;
- le statut de la FAQ dans le registre.

Le chunking, le reranker, la génération et le prompt sont les mêmes. Le top 5 change pour 26 questions, dont les 20 qui avaient un chunk `projet` dans leur top 5 au n° 15 (21 chunks au total). 101 réponses sur 127 sont identiques.

#### Résultats (n° 15 → n° 16)

| | n° 15 | n° 16 |
|---|---|---|
| hit@5 | 0,943 | 0,943 |
| MRR | 0,847 | **0,855** |
| recall@5 | 0,918 | 0,918 |
| nDCG@5 | 0,839 | **0,845** |
| Refus à tort | 4/122 (3,3 %) | 4/122 (3,3 %) |
| correctness (31) | 0,784 | 0,777 |
| faithfulness (31) | 0,968 | 0,919 |
| **`trap_hit`** | **7/17** | **4/17** |
| `trap_avoided` selon le juge | 15/17 (0,88) | 15/17 (0,88) |
| Réponses qui reprennent le piège, après relecture | 0/17 | 0/17, et 1 cas limite (Q023) |
| Chunks `projet` dans les top 5 | 21 | 0 |
| Tokens envoyés au LLM par question (moyenne) | 1 806 | 1 807 |
| Temps de réponse moyen / médian / 90e centile | 6,19 s / 5,48 s / 9,8 s | 6,24 s / 5,61 s / 9,3 s |
| Durée du run | 266 s | 268 s |

#### Les pièges

**Le piège sort du top 5 pour Q026, Q027 et Q089**, comme prévu. Les trois réponses restent justes :
- Q026 : un loyer de 23,50 €/m² ;
- Q027 : une prise de fonctions le 15 juin 2026 ;
- Q089 : 18 110 €.

Pour Q023 et Q049, la preuve passe du 2e au 1er rang, puisque le projet de PV qui la précédait a disparu. C'est le gain de MRR.

**Le cas limite de Q023.** Le projet de PV est écarté, mais le **PV signé** du 18/11 (statut `valide`) contient lui aussi « investissement de 1,2 M€ ». La réponse change d'ordre :
- au n° 15 : « … un montant de 1 250 000 € …, une correction apportée lors de la séance du 16 décembre 2025 par rapport aux 1,2 M€ initialement mentionnés » ;
- au n° 16 : « … a approuvé un investissement de 1,2 M€ … lors de la réunion du 18 novembre 2025. Toutefois, lors de la séance du 16 décembre 2025, le procès-verbal a été approuvé avec une correction précisant que l'enveloppe approuvée est de 1 250 000 € ».

La valeur finale est juste, mais la réponse commence par la valeur piège. Le juge note `trap_avoided` à 1 et baisse la faithfulness à 0,5. Je ne la compte pas comme un piège repris, mais comme un cas limite. C'est ce que vise la consigne « un PV corrigé est remplacé par celui qui le corrige » de l'étape suivante.

**Les 4 pièges restants sont hors de portée d'un filtre sur le statut :**

| Question | Document du piège | Statut |
|---|---|---|
| Q023 | PV CA 2025-11-18 signé (1,2 M€, corrigé le 16/12) | `valide` |
| Q043 | Budget 2026 v1 et v2 (la bonne réponse est le budget approuvé) | aucun |
| Q048 | Politique télétravail v2 (2023), remplacée par la v3 (2026) | aucun |
| Q153 | Plan stratégique 2026-2028 v1 (190 M€ au lieu de 185 M€) | aucun |

Écarter aussi les versions remplacées serait risqué. Les questions `decision_history` ont besoin des épisodes anciens :
- Q066 demande le montant d'abord soumis au conseil (1 400 000 €, revu ensuite) ;
- Q092 demande la limite d'avant l'accident, tirée d'un PV archivé.

Choisir entre les versions est donc laissé au modèle (étapes suivantes).

#### Les autres changements

Parmi les 20 questions qui avaient un chunk `projet`, les réponses qui changent restent équivalentes. Certaines sont un peu plus précises (Q002, Q013, Q151).

Les variations de correctness suivent des réponses reformulées, et restent dans le bruit habituel :

| Question | correctness |
|---|---|
| Q002, Q013 | +0,1 |
| Q018, Q024 | −0,1 |
| Q158 | −0,2 |

Q116 (`out_of_corpus`) perd sa note de faithfulness (de 1 à 0) pour une réponse identique au n° 15. C'est le bruit du juge, déjà vu au n° 14.

#### Coût

Aucun : le filtre ne change ni les tokens ni le temps de réponse.

#### Décision : le filtre sur le statut est conservé

Il ôte 3 pièges sur 7 du top 5, fait avancer deux preuves au 1er rang, ne perd aucune preuve et ne coûte rien. Le taux de pièges passe de 7/17 à 4/17 pour `trap_hit`, et reste à 0/17 réponse qui reprend le piège, avec un cas limite.

### Étape 2 : des consignes de lecture dans le prompt (n° 17)

#### Le changement testé

Le nouveau prompt, `prompts/detailed_fr_versions.txt`, part de `detailed_fr.txt` (section 4). Les autres consignes sont identiques, simplement renumérotées. La consigne 3 est précisée, et deux consignes sont ajoutées :

> 3. Lorsqu'une information a changé au fil du temps, donne la plus récente selon les dates des documents. **Si la question porte sur une date ou une période passée, ou sur ce qui avait d'abord été décidé, donne la valeur de ce moment-là.**
> 4. **Un projet de document ou une version de travail (v1, v2…) ne fait pas foi : préfère la version signée, approuvée ou définitive.**
> 5. **Lorsqu'un procès-verbal est corrigé lors de son approbation à une séance suivante, la correction remplace la valeur d'origine : donne la valeur corrigée comme réponse, et ne présente jamais la valeur d'origine comme la décision prise.**

Ce sont les trois règles du TODO : la décision la plus récente prime, un projet ne fait pas foi, un PV corrigé est remplacé.
- **La consigne 3** existait déjà en partie. L'exception ajoutée protège les questions `decision_history`, qui demandent une valeur ancienne.
- **La consigne 4** vise Q043, Q048 et Q153. Les lignes de contexte donnent déjà la version : `[Budget 2026 (v1) · …]`, `[Plan strategique 2026-2028 v1 · …]`.
- **La consigne 5** vise le cas limite de Q023.

#### Comparabilité

Entre les commits `6010c97` (n° 16) et `ec9f7b9` (n° 17), en dehors du rapport et de l'export CSV, seuls ont changé le prompt et le TOML. L'index n'a pas été reconstruit.

Le top 5 ne change que pour Q033 et Q121, où deux passages aux scores de reranking presque égaux (0,7773 et 0,7771) échangent leur place. C'est un arrondi du reranker. 89 réponses sur 127 sont identiques.

#### Résultats (n° 16 → n° 17)

| | n° 16 | n° 17 |
|---|---|---|
| hit@5 / MRR / recall@5 / nDCG@5 | 0,943 / 0,855 / 0,918 / 0,845 | identiques |
| Refus à tort | 4/122 (3,3 %) | 4/122 (3,3 %) |
| correctness (31) | 0,777 | 0,771 |
| faithfulness (31) | 0,919 | 0,892 |
| `trap_hit` | 4/17 | 4/17 |
| `trap_avoided` selon le juge | 15/17 (0,88) | 15/17 (0,88) |
| **Réponses qui reprennent le piège, après relecture** | 0/17, et 1 cas limite (Q023) | **0/17, sans cas limite** |
| Tokens envoyés au LLM par question (moyenne) | 1 807 | 1 934 |
| Temps de réponse moyen / médian / 90e centile | 6,24 s / 5,61 s / 9,3 s | 6,29 s / 5,59 s / 10,2 s |
| Durée du run | 268 s | 271 s |

Le changement ne touche que la génération, et le juge ne note que 2 questions par type. J'ai donc relu les réponses aux 17 questions avec piège et aux 6 questions `decision_history`.

- **Q023 est réglée.** La réponse commence maintenant par la bonne valeur : « … un montant de 1 250 000 € pour la phase 1 de la ligne L4, une valeur corrigée lors de l'approbation du procès-verbal du 16 décembre 2025 ». La faithfulness passe de 0,5 à 1.
- **L'exception de la consigne 3 tient** : les 6 réponses `decision_history` restent justes. Le meilleur test est Q138 (« combien d'interventions du rappel avaient été réalisées **au 26 janvier 2026** ? »). La réponse donne toujours « 168 sur 214 », c'est-à-dire la valeur piège de Q008, qui porte sur l'état actuel. La consigne 3 n'a pas poussé le modèle vers la valeur la plus récente.
- **Les autres questions avec piège restent justes** (Q026, Q027, Q043, Q048, Q089, Q091, Q096, Q099, Q108, Q133, Q153…).
  - Q008 reste incomplète.
  - Q056 reste fausse, à cause du tableau de l'organigramme (section 6).
- **Un effet secondaire : trois réponses perdent leur justification.**
  - Q048 ne précise plus « selon la version 3 de la politique ».
  - Q133 ne parle plus de la succession.
  - Q153 ne dit plus « selon le plan stratégique le plus récent ».

  Elles restent justes. Le 0,7 → 0,6 de Q153 en correctness vient de là.
- **Le reste du recul des moyennes est du bruit du juge** :
  - Q082 (`out_of_corpus`) : la faithfulness passe de 1 à 0, pour un refus identique ;
  - Q152 : la correctness passe de 0,2 à 0, pour une réponse de même contenu ;
  - Q158 : la faithfulness passe de 1 à 0,67.

#### Coût

Le prompt plus long ajoute 127 tokens par question (+7 %). Le temps de réponse moyen ne bouge presque pas : +0,05 s.

#### Ce qui reste faux ne vient plus de la lecture

Trois questions sur des fils de décision restent fausses, parce que le dernier épisode du fil n'arrive pas au LLM :
- **Q008** : la clôture du rappel au 31 mars 2026 manque ;
- **Q152** : l'accord de Valtek (65 % du coût) manque, et la réponse donne l'action « en retard » ;
- **Q081** : la réponse est juste (725 k€), mais elle est tirée des PV de COPIL, sans la preuve de grade 2.

J'ai relancé la recherche de ces trois questions avec 30, 60 et 100 candidats :

| Question | Rangs des preuves dans la recherche (30 candidats) | Rangs après reranking (30 candidats) | Avec 60 ou 100 candidats |
|---|---|---|---|
| Q008 | 14, 20 | 9, 14 | 10, 11, 17 |
| Q152 | 3, 5, 11 | 1, 8, 16 | 1, 8, 17 |
| Q081 | 18, 30 | 16, 17 | 16, 17 |

**Les preuves sont déjà parmi les 30 candidats.** C'est le reranker qui les classe après le 5e rang. Prendre 60 ou 100 candidats, comme le proposait l'étape 5 du TODO, ne change rien. Trier les passages par date (étape 3) ou les filtrer par date (étape 4) non plus : ces pistes n'agissent que sur les passages déjà transmis au LLM, et les 6 questions `decision_history` sont déjà justes.

#### Décision : les consignes sont conservées

1. Elles règlent le seul cas limite (Q023), sans régression sur les questions d'historique.
2. Elles coûtent 7 % de tokens, sans effet sur le temps de réponse.

Le gain est modeste parce que les réponses aux questions avec piège étaient déjà presque toutes justes. Le taux de pièges est de 4/17 pour `trap_hit`, et de 0/17 réponse qui reprend le piège.

La suite vise le classement : faire lire plus de passages au LLM (`top_k` de 5 à 10), pour Q008 et Q152.

## Évaluation finale sur la réserve de test (`v1.0`)
_À compléter : réserve de test (31 questions) comparée au jeu de développement._

## Trois questions ratées par la meilleure configuration
_À compléter : étape où se situe l'échec (inventaire, conversion, chunking, recherche, reranking, génération) et piste de correction._
