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
4. un prompt qui impose une réponse en français (à venir), ajouté à la configuration n° 4.

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

### Étape 4 : prompt « réponds en français »
_À compléter._

## Section 5 : les fichiers Excel (`v0.4-excel`)
_À compléter._

## Section 6 : les images et les scans (`v0.5-images`)
_À compléter : temps total de lecture, taux d'erreur mesuré sur dix transcriptions._

## Section 7 : le temps et les versions (`v0.6-versions`)
_À compléter : taux de pièges avant (section 3 : 1/17) et après._

## Évaluation finale sur la réserve de test (`v1.0`)
_À compléter : réserve de test (31 questions) comparée au jeu de développement._

## Trois questions ratées par la meilleure configuration
_À compléter : étape où se situe l'échec (inventaire, conversion, chunking, recherche, reranking, génération) et piste de correction._
