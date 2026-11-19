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

- La durée est celle du run complet (127 questions).
- Le modèle a refusé toutes les questions `out_of_corpus` (5/5), dans les deux expériences.

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
