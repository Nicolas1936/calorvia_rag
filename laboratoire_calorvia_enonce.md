# Laboratoire — Un assistant documentaire pour Calorvia

Ce laboratoire reprend tout le module sur un cas proche de la réalité : le disque partagé d'une entreprise de 620 personnes. Les employés veulent poser leurs questions en français et obtenir une réponse sourcée : « Quand le nouvel ERP démarre-t-il ? », « Qui est responsable de l'action A-26-008 ? », « Quelle vitesse est autorisée dans l'entrepôt de Gand ? ».

Vous réutilisez tout ce que vous avez construit :

- la conversion avec Docling ;
- le chunking ;
- la recherche hybride et le reranking ;
- la génération ;
- l'évaluation (métriques déterministes et LLM juge) ;
- l'enregistrement des expériences dans PostgreSQL (exercice 3) ;
- la maintenance de l'index : versions, doublons et langues (chapitre 05).

Quatre choses sont nouvelles :

1. **les fichiers Excel**, jamais abordés jusqu'ici ;
2. **les images et les scans**, à lire avec un modèle de vision (VLM) ;
3. **plusieurs langues** dans le corpus (français, néerlandais, anglais) ;
4. **Git, obligatoire**, avec un dépôt distant sur GitHub.

Le notebook `labo_calorvia_pistes.ipynb` donne des pistes, avec du code exécuté sur le corpus, pour les langues, les fichiers Excel et les images.

## Ce que vous recevez

| Fichier                        | Contenu                                                                                                         |
| ------------------------------ | --------------------------------------------------------------------------------------------------------------- |
| `calorvia_dataset.zip`       | `corpus/calorvia/` : les 393 documents ; `corpus/calorvia_eval.json` : le jeu d'évaluation (158 questions) |
| `labo_calorvia_pistes.ipynb` | Le notebook de pistes : à ranger dans `notebooks/`                                                           |

Contrairement à l'hôpital, **aucun fichier ne décrit les documents** : à vous d'extraire les métadonnées (date, type, version, langue) à partir des chemins, des noms de fichiers et du contenu. Cela fait partie du travail.

## Les services

Les mêmes que dans le cours, plus un modèle de vision :

| Port | Service                                        | Modèle                                                           |
| ---- | ---------------------------------------------- | ----------------------------------------------------------------- |
| 8000 | LLM (llama-server)                             | celui du cours                                                    |
| 8001 | Embedder (vLLM)                                | bge-m3, ou le meilleur de l'exercice 3                            |
| 8002 | Reranker (vLLM)                                | bge-reranker-v2-m3, ou le meilleur de l'exercice 3                |
| 8003 | **VLM** (llama-server avec `--mmproj`) | par exemple Qwen3-VL-8B-Instruct (GGUF et son fichier `mmproj`) |

Le VLM ne sert qu'à l'ETL, pour lire les images une fois. Si la mémoire du GPU ne suffit pas pour tout faire tourner en même temps, arrêtez le LLM pendant cette étape.

---

## Le jeu de données : Calorvia SA

**Tout est inventé** : l'entreprise, les personnes, les clients, les fournisseurs, les chiffres.

Calorvia SA fabrique des pompes à chaleur (gamme Aéris) et des groupes de ventilation (gamme Ventis). Elle compte environ 620 personnes et a réalisé 148,2 M€ de chiffre d'affaires en 2025. Les documents couvrent **septembre 2025 à juin 2026**.

| Site    | Rôle                                                     | Langue des documents |
| ------- | --------------------------------------------------------- | -------------------- |
| Namur   | Siège : direction, finance, RH, informatique, commercial | français            |
| Seneffe | Usine des pompes à chaleur (lignes L1 à L3, puis L4)    | français            |
| Gand    | Usine de ventilation et entrepôt                         | néerlandais         |
| Lille   | Bureau commercial France                                  | français            |
| Herstal | Entrepôt ouvert en mai 2026                              | français            |

Le comité de direction (CODIR), qui se réunit chaque lundi, est composé des membres suivants.

| Personne            | Fonction                                                        |
| ------------------- | --------------------------------------------------------------- |
| Hélène Marchal    | Administratrice déléguée (CEO)                               |
| Laurent Dewit       | Directeur financier, jusqu'au 31 mars 2026                      |
| Sarah Vandamme      | Directrice financière ad interim, du 1er avril au 14 juin 2026 |
| Isabelle Gérard    | Directrice financière, depuis le 15 juin 2026                  |
| Thomas Lambert      | Directeur des opérations                                       |
| Nadia Benali        | Directrice RH                                                   |
| Pierre-Yves Collard | Directeur commercial                                            |
| Kevin Mertens       | Directeur des SI                                                |
| Anne Vercammen      | Directrice qualité                                             |
| Pieter De Smet      | Directeur du site de Gand                                       |

Le conseil d'administration (CA) se réunit une fois par mois.

### Les formats

| Format      | Fichiers | Comment le lire                                                                                            |
| ----------- | -------- | ---------------------------------------------------------------------------------------------------------- |
| DOCX        | 156      | Docling                                                                                                    |
| PDF natif   | 76       | Docling. Deux PDF contiennent des graphiques dont les valeurs ne sont pas dans le texte                    |
| PDF scanné | 9        | **Aucune couche texte** : OCR ou VLM                                                                 |
| XLSX        | 55       | À lire vous-même (notebook, partie 2)                                                                    |
| HTML        | 31       | Docling                                                                                                    |
| JPG         | 31       | VLM : photos de plaques signalétiques et de tableaux blancs, factures et bons de livraison photographiés |
| PNG         | 23       | VLM : organigrammes, plans, graphiques, plannings, schémas                                                |
| PPTX        | 9        | Docling                                                                                                    |
| CSV         | 2        | Docling ou polars                                                                                          |
| Markdown    | 1        | Docling                                                                                                    |

Répartition par langue : 342 documents en français, 44 en néerlandais (dont 6 images) et 7 en anglais.

```text
calorvia/
├── 00_Direction/         CODIR (2025, 2026, annexes), conseil d'administration (PV signés,
│                         projets de PV, convocations, AG), stratégie, modèles
├── 01_Finance/           budget 2026, reporting mensuel, investissements, factures scannées, trésorerie
├── 02_RH/                politiques, notes de service, offres d'emploi, formation, effectifs,
│                         organigrammes, enquête, Confidentiel/
├── 03_Production/        Seneffe, Gent (en néerlandais), maintenance, procédures, plans
├── 04_Qualite/           non-conformités, rappel de l'Aéris 12, audit ISO, réclamations, indicateurs
├── 05_Commercial/        tarifs, fiches produits FR/NL/EN, offres de prix, comptes clés, tableaux de bord
├── 06_Achats/            contrats fournisseurs (en anglais), appel d'offres ERP, bons de livraison
├── 07_IT/                projet ERP Atlas (COPIL, plannings, documentation), sécurité, architecture, support
├── 08_Juridique/         bail, contrats, RGPD, assurance
├── 09_Communication/     newsletters, communiqués FR/NL/EN, pages intranet
├── 10_RSE/               bilan carbone, rapport RSE
└── 99_Archives/          2024, Doublons/, Divers/
```

### Les documents qui se suivent

| Série                                    | Nombre                                    | Ce que chaque document contient                                                                                                                                                                                                         |
| ----------------------------------------- | ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PV du CODIR                               | 41 séances                               | Présents, indicateurs de la semaine, **tableau de suivi des actions**, points de l'ordre du jour, décisions numérotées (D-26-08), nouvelles actions (A-26-012), tour de table. Chaque PV rappelle des décisions antérieures |
| PV du CA                                  | 10 séances                               | Approbation du PV précédent (parfois avec une correction), situation financière, résolutions. Les quatre PV de 2025 sont des **scans signés**                                                                                |
| COPIL du projet ERP                       | 14                                        | État de chaque chantier, indicateurs, points marquants                                                                                                                                                                                 |
| Comités de sécurité                    | 9 à Gand (en néerlandais), 3 à Seneffe | Accidents, absentéisme, suivi des mesures                                                                                                                                                                                              |
| Reporting mensuel, rapports de production | 9, 9 + 9                                  | Classeurs Excel à plusieurs onglets                                                                                                                                                                                                    |
| Newsletter                                | 10                                        | Reprend les nouvelles du mois                                                                                                                                                                                                           |

Dans le tableau de suivi des actions, une action est « En cours », passe « En retard » si son échéance est dépassée, puis « Clôturée » avec un commentaire. On suit donc une action d'un PV au suivant.

### Les dix fils de décision

Dix sujets évoluent au fil des réunions. La bonne réponse dépend donc de la date, et les anciennes valeurs restent dans le corpus.

| Fil (`thread`) | Ce qui change                                                                                         |
| ---------------- | ----------------------------------------------------------------------------------------------------- |
| `erp`          | Choix de l'éditeur, budget, date de mise en production reportée, démarrage en deux temps           |
| `l4`           | Montant de la nouvelle ligne de production, report par le CA, aide régionale, retard de livraison    |
| `price`        | Hausse tarifaire 2026 proposée, puis décidée autrement, et une exception pour un client            |
| `telework`     | Un jour par semaine, puis un pilote à deux jours, puis la généralisation avec de nouvelles règles |
| `accident`     | Vitesse des chariots à Gand, modifiée deux fois après un accident                                  |
| `recall`       | Rappel d'un produit, avancement semaine après semaine, partage des coûts avec le fournisseur        |
| `cyber`        | Tentative de fraude, double authentification obligatoire, échéance reportée pour certains postes   |
| `herstal`      | Location d'un entrepôt, conditions du bail, date d'ouverture reportée                               |
| `freeze`       | Gel des recrutements, décidé puis levé                                                             |
| `cfo`          | Départ du directeur financier, intérim, nomination d'une successeure                                |

Les réponses attendues sont dans le jeu d'évaluation.

---

## Les pièges du corpus

Le corpus a été construit pour piéger un RAG naïf. Les voici tous. Les connaître ne suffit pas : votre système doit les déjouer.

| Piège                                                    | Où                                                                                                                                                                                                                                                                 | Ce qui se passe si on tombe dedans                                                                                                      |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| **Décisions qui changent**                         | Les dix fils ci-dessus                                                                                                                                                                                                                                              | Le RAG répond avec une valeur dépassée (la date initiale de l'ERP, l'ancienne limite de vitesse)                                     |
| **Rappels des anciennes valeurs**                   | PV du CODIR (« Pour rappel, la mise en production avait été fixée au 1er avril »), newsletters, PV du CA                                                                                                                                                       | Le bon chunk contient aussi la mauvaise valeur ; un chunk ancien ressemble beaucoup à la question                                      |
| **Erreur corrigée dans le PV suivant**             | Le PV du CA du 18/11/2025 (scanné) écrit 1,2 M€ pour la ligne L4 ; le PV du 16/12/2025 corrige le montant en l'approuvant                                                                                                                                        | Seul le PV de décembre donne le bon montant, et il faut lire les deux                                                                  |
| **Brouillon contre version signée**                | `00_Direction/Conseil_administration/Projets_PV/` : le projet du 18/11 contient la même erreur ; celui du 17/02 indique un autre loyer pour Herstal ; celui du 19/05 une autre date d'entrée en fonction                                                        | Le brouillon est un document « propre » (DOCX), plus facile à lire que le PV signé                                                  |
| **Deux versions d'un même PV**                     | `PV_CODIR_2025-11-17.docx` (version 1 : date de l'accident fausse) et `PV_CODIR_2025-11-17_v2.docx`                                                                                                                                                             | Les deux sont presque identiques                                                                                                        |
| **Versions successives**                            | Budget 2026 v1, v2 et approuvé ; tarif 2026 projet v1 et final ; politique de télétravail v1 (archives), v2 et v3 ; procédure MFA v1 et v2 ; plan stratégique v1 et final ; organigrammes 2024, 2025-09, 2026-04, 2026-06 ; plannings du projet ERP v1, v2, v3 | Le contexte mélange les versions                                                                                                       |
| **Nom de fichier trompeur**                         | `99_Archives/Doublons/Budget 2026 v2 FINAL.xlsx` contient la version 2, pas le budget approuvé                                                                                                                                                                   | Le mot « FINAL » attire la recherche lexicale                                                                                         |
| **Doublons exacts**                                 | `99_Archives/Doublons/` (copies de fichiers), la grille d'évaluation ERP en annexe du CODIR et aux achats, le rapport 8D en annexe et en qualité, la politique de télétravail v3 en DOCX et en PDF                                                            | Les mêmes chunks occupent plusieurs places du top k                                                                                    |
| **Même information dans trois langues**            | Les communiqués de presse en français, néerlandais et anglais                                                                                                                                                                                                    | Doublons qui ne se ressemblent pas lexicalement                                                                                         |
| **Archives**                                        | `99_Archives/2024/` : un PV de CODIR de 2024, le tarif 2024, le budget 2025, l'organigramme 2024                                                                                                                                                                  | Des valeurs anciennes, parfois encore plausibles                                                                                        |
| **Néerlandais et anglais**                         | `03_Production/Gent/`, contrats fournisseurs, fiches produits, communiqués                                                                                                                                                                                       | Question en français, réponse dans une autre langue : la recherche lexicale ne trouve rien                                            |
| **Scans sans couche texte**                         | Les 4 PV du CA de 2025, l'avenant Distrinergie, l'attestation d'assurance, deux courriers de clients, `99_Archives/Divers/scan0001.pdf`                                                                                                                           | Sans OCR, le document est vide ; avec l'OCR de Docling, la qualité dépend du moteur et des langues configurées                       |
| **Information seulement dans une image**            | Organigrammes (qui dépend de qui), plaques signalétiques (numéros de série), plans (point de rassemblement), tableaux blancs, graphiques, plannings, schémas d'architecture, factures et bons de livraison (avec des annotations manuscrites)                  | Sans VLM, la réponse est introuvable                                                                                                   |
| **Graphique dans un PDF**                           | `00_Direction/CODIR/Annexes/2026-04-13 Annexe - Resultats enquete teletravail.pdf`, `10_RSE/Rapport RSE 2025.pdf`                                                                                                                                               | Le texte du PDF ne contient pas les valeurs du graphique                                                                                |
| **Excel vu par Docling**                            | Tous les classeurs                                                                                                                                                                                                                                                  | Pourcentages en décimal (`-0.00681316572305923`), titre fusionné recopié dans chaque colonne, nom de l'onglet perdu, unité perdue |
| **Questions de calcul**                             | Questions `excel_reasoning`                                                                                                                                                                                                                                       | Comparer ou chercher un maximum sur plusieurs lignes ou fichiers : le LLM se trompe facilement                                          |
| **Information dans un tableau de suivi**            | Le statut d'une action n'existe que dans le tableau « Suivi des actions » d'un PV                                                                                                                                                                                 | Le chunk de tableau doit garder son en-tête et la date de la séance                                                                   |
| **Noms de fichiers incohérents**                   | Voir la section 2                                                                                                                                                                                                                                                   | Une seule expression régulière ne suffit pas pour extraire les dates                                                                  |
| **Date du fichier différente de celle du contenu** | Photos `IMG_20260311_...jpg` : date de la photo, pas de la machine                                                                                                                                                                                                | La date du nom de fichier ne veut pas toujours dire la même chose                                                                      |
| **Contenu répété**                               | Pied de page de tous les DOCX et PDF, en-tête et pied de page de l'intranet, rubriques fixes des newsletters, paragraphe « À propos de Calorvia » des communiqués                                                                                              | Des chunks presque identiques, sans information                                                                                         |
| **Données personnelles**                           | `02_RH/Confidentiel/Entretiens annuels 2025 - synthese.xlsx` : noms, évaluations, augmentations                                                                                                                                                                  | Un RAG qui les indexe les révèle à quiconque pose la question                                                                        |
| **Fichiers sans intérêt**                         | Modèles vierges (`00_Direction/Modeles/`), `99_Archives/Divers/` (document vide, `test.xlsx`, `Document1.docx`, un menu de cantine scanné)                                                                                                                | Du bruit dans l'index                                                                                                                   |
| **Questions hors corpus à la prémisse plausible** | 6 questions `out_of_corpus`, dont une sur un ERP utilisé « avant 2011 »                                                                                                                                                                                        | Le LLM invente une réponse à partir d'un chunk voisin                                                                                 |

---

## Le jeu d'évaluation

`calorvia_eval.json` contient 158 questions, au format de l'hôpital, avec trois différences :

- `document` est le **chemin relatif** du fichier dans `corpus/calorvia/` (deux fichiers peuvent avoir le même nom). Mettez ce chemin dans le payload de vos chunks ;
- un champ **`traps`** liste, pour 21 questions, les passages qui contiennent une réponse **fausse ou dépassée** : brouillon, ancienne version, PV corrigé plus tard ;
- les champs `thread` (le fil de décision), `difficulty` (`facile`, `moyen`, `difficile`) et `notes` (le piège visé, quand il y en a un).

```json
{
  "id": "Q023",
  "type": "board_resolution",
  "thread": "l4",
  "question": "Quel montant le conseil d'administration a-t-il approuvé pour la phase 1 de la ligne L4 ?",
  "answer": "1 250 000 €. Le procès-verbal du 18 novembre 2025 indique 1,2 M€ par erreur ; il a été corrigé lors de l'approbation du PV au conseil du 16 décembre 2025.",
  "evidence": [
    {"document": "00_Direction/Conseil_administration/PV_signes/PV CA 2025-12-16 signé.pdf",
     "snippets": ["1 250 000", "non de 1,2"], "grade": 2, "fact": 0},
    {"document": "00_Direction/CODIR/2025/PV_CODIR_2025-11-17_v2.docx",
     "snippets": ["L'enveloppe révisée de 1 250 000 € pour la phase 1 de la ligne L4 est soumise au CA du 18 novembre."],
     "grade": 2, "fact": 0}
  ],
  "traps": [
    {"document": "00_Direction/Conseil_administration/PV_signes/PV CA 2025-11-18 signé.pdf",
     "snippets": ["investissement de 1,2"]},
    {"document": "00_Direction/Conseil_administration/Projets_PV/Projet PV CA 2025-11-18.docx",
     "snippets": ["l'investissement de 1,2 M€ pour la phase 1 de la ligne L4"]}
  ],
  "difficulty": "difficile",
  "notes": "Piège : l'erreur figure dans le PV signé (scanné) de novembre et est corrigée dans le PV suivant."
}
```

| Type                  | Nombre | Ce que la question teste                                                  |
| --------------------- | ------ | ------------------------------------------------------------------------- |
| `decision_current`  | 15     | L'état actuel d'une décision qui a changé                              |
| `decision_history`  | 10     | L'état d'une décision à une date passée (« En décembre 2025, … ») |
| `decision_reason`   | 8      | La raison d'une décision                                                 |
| `action_tracking`   | 12     | Responsable, échéance et statut d'une action du CODIR                   |
| `meeting_detail`    | 10     | Présence, présidence, indicateur d'une séance précise                 |
| `board_resolution`  | 8      | Résolutions du conseil d'administration                                  |
| `excel_lookup`      | 16     | Une valeur dans un classeur                                               |
| `excel_reasoning`   | 6      | Une comparaison ou un maximum dans un tableau                             |
| `image_only`        | 15     | Une information présente seulement dans une image                        |
| `image_in_document` | 2      | Une valeur lisible seulement dans un graphique d'un PDF                   |
| `scan_ocr`          | 8      | Un scan ou une photo de document                                          |
| `multilingual`      | 10     | Une réponse dans un document néerlandais ou anglais                     |
| `version_trap`      | 6      | La bonne version d'un document                                            |
| `multi_doc`         | 8      | Des faits de plusieurs documents à combiner                              |
| `factual`           | 18     | Un fait simple                                                            |
| `out_of_corpus`     | 6      | Pas de réponse dans le corpus : la bonne réponse est un refus           |

### Une réserve de test

Gardez de côté les **31 questions dont le numéro est un multiple de 5** (Q005, Q010… Q155). Pendant tout le laboratoire, vous réglez votre système sur les 127 autres questions (le jeu de développement), sans regarder ces 31-là. À la fin seulement, vous évaluez la configuration retenue sur la réserve. Si les scores y sont nettement plus bas, vous avez réglé votre système sur les questions plutôt que sur le problème.

```python
test_ids = {q["id"] for q in questions if int(q["id"][1:]) % 5 == 0}
```

Autre règle, pour la même raison : le jeu d'évaluation sert à **mesurer**, jamais à construire. Pas de réponse attendue dans un prompt, pas de règle écrite pour une question précise.

### Les mesures

- **Métriques déterministes** (hit rate, MRR, recall, nDCG) sur les questions avec preuves du jeu de développement, pour chaque expérience.
- **LLM juge** sur un échantillon de deux questions par type du jeu de développement (31 questions), pour les changements qui touchent la génération et pour les configurations retenues.
- **Refus** sur les questions `out_of_corpus`, et refus à tort sur les autres.
- **Nouveau : les pièges.** Pour les questions qui ont des `traps`, la part des questions dont au moins un piège remonte dans le top k (plus c'est bas, mieux c'est) ; et, avec le juge, la part des réponses qui reprennent la valeur du piège.

```python
def trap_hit(chunks, question):
    """True if a retrieved chunk contains a wrong or outdated answer listed in `traps`."""
    return any(
        chunk["document"] == trap["document"]
        and all(normalize(snippet) in normalize(chunk["text"]) for snippet in trap["snippets"])
        for chunk in chunks for trap in question["traps"]
    )
```

Deux précisions sur la vérité terrain :

- **Les nombres.** Les extraits de preuve des classeurs suivent le rendu de Docling (`4568`, `41.5`). Si vos chunks affichent les nombres autrement (`4 568`, `41,5`), ajoutez à `normalize()` une normalisation des nombres, appliquée au chunk et à l'extrait. Faites-le dès le début, pour toutes les expériences :

```python
import re

def normalize_numbers(text):
    """'4 568' -> '4568', '41,5' -> '41.5': the same rendering in chunks and evidence snippets."""
    text = re.sub(r"(?<=\d)[   ](?=\d{3}\b)", "", text)
    return re.sub(r"(?<=\d),(?=\d)", ".", text)
```

- **Les images.** Les extraits de preuve des images et des scans sont courts (un numéro, un nom, un nombre), mais la transcription d'un VLM ne reprend pas toujours exactement la mise en forme de l'image. Pour ces questions, la note du juge compte plus que le recall.

---

## Les règles du jeu

- **Git est obligatoire** (section 0) : l'historique du dépôt fait partie de l'évaluation.
- **Repartez de l'application de l'exercice 3**, dans un nouveau dépôt `rag-calorvia`, avec la même structure.
- **Une version de référence d'abord**, puis **un seul changement à la fois**.
- **Toute expérience est enregistrée** dans PostgreSQL, avec le commit Git qui l'a produite.

---

## 0. Git et GitHub

### Le dépôt

Créez sur GitHub un dépôt **privé** nommé `rag-calorvia` et invitez le formateur comme collaborateur (*Settings*, puis *Collaborators* ; son identifiant GitHub vous sera communiqué en séance).

Sur la machine du cours, une clé SSH évite de taper un mot de passe à chaque `push` :

```bash
git config --global user.name "Prénom Nom"
git config --global user.email "adresse@exemple.com"     # the email address of your GitHub account

ssh-keygen -t ed25519 -C "adresse@exemple.com"           # press Enter to accept the default file
cat ~/.ssh/id_ed25519.pub                                # copy this line into GitHub: Settings > SSH and GPG keys
ssh -T git@github.com                                    # must answer "Hi <your login>!"
```

Puis, dans le dossier du projet :

```bash
git init -b main
git add .
git commit -m "Create project structure"
git remote add origin git@github.com:<votre-login>/rag-calorvia.git
git push -u origin main
```

### Ce qui va dans Git, et ce qui n'y va pas

| Dans Git                                                                                 | Hors de Git (`.gitignore`)                                                                |
| ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| Le code (`src/`, `scripts/`), `pyproject.toml`, `uv.lock`                        | Le corpus et le jeu d'évaluation (`data/`)                                               |
| Les configurations d'expériences (`experiments/*.toml`) et les prompts (`prompts/`) | `.env` (mots de passe, URL)                                                               |
| `.env.example`, `docker-compose.yml`                                                 | L'environnement Python (`.venv/`)                                                         |
| Les notebooks, sans leurs sorties volumineuses                                           | Les conversions Docling, les transcriptions du VLM, les données de Qdrant et de PostgreSQL |
| `README.md`, `RAPPORT.md`, les exports de résultats (`results/*.csv`)             | Les modèles (`~/models`, de toute façon hors du projet)                                 |

```text
# .gitignore
.env
.venv/
__pycache__/
.ipynb_checkpoints/
data/
qdrant_storage/
*.log
```

Si un `.env` a été commis par erreur : changez les mots de passe concernés, puis `git rm --cached .env` et un nouveau commit. Le fichier reste visible dans l'historique : c'est pour cela qu'il faut changer les mots de passe.

### Comment travailler

- **De petits commits, souvent**, chacun avec un message qui dit ce qu'il fait, en anglais et à l'impératif : `Add Excel row chunker`, `Fix date extraction for CODIR 2026 files`. Pas de commit unique « final » la veille du rendu.
- **Une branche par piste** (`feat/excel`, `feat/vlm`, `feat/versions`), fusionnée dans `main` une fois évaluée :

```bash
git switch -c feat/excel            # new branch
# ... commits ...
git switch main
git merge feat/excel
git push
```

- **Un tag à chaque étape**, poussé sur GitHub :

```bash
git tag -a v0.2-baseline -m "Baseline: text documents only"
git push origin --tags
```

| Tag                 | Étape                                        |
| ------------------- | --------------------------------------------- |
| `v0.1-inventaire` | Sections 1 et 2 : inventaire et métadonnées |
| `v0.2-baseline`   | Section 3 : version de référence            |
| `v0.3-langues`    | Section 4                                     |
| `v0.4-excel`      | Section 5                                     |
| `v0.5-images`     | Section 6                                     |
| `v0.6-versions`   | Section 7                                     |
| `v1.0`            | Le rendu                                      |

### Relier chaque expérience à son commit

Une expérience n'est reproductible que si l'on sait avec quel code elle a tourné. Ajoutez deux colonnes à la table `experiments` de l'exercice 3 :

```sql
ALTER TABLE experiments ADD COLUMN git_commit TEXT, ADD COLUMN git_dirty BOOLEAN;
```

```python
import subprocess

def git_state():
    """Current commit, and whether the working tree has uncommitted changes."""
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True).stdout != ""
    return commit, dirty
```

Règle : une expérience dont les résultats figurent dans le rapport tourne sur un code commité (`git_dirty = false`).

---

## 1. Le projet et l'inventaire

Partez de l'arborescence de l'exercice 3. Ajoutez au moins :

```text
src/rag_calorvia/
├── etl/
│   ├── inventory.py      # walk the corpus, one row per file in PostgreSQL
│   ├── metadata.py       # dates, types, versions, languages (section 2)
│   ├── excel.py          # workbooks -> chunks (section 5)
│   └── vision.py         # images and scans -> transcriptions, with a cache (section 6)
└── ...
```

**L'inventaire** parcourt le corpus et enregistre une ligne par fichier dans une table `documents` : chemin relatif, format, taille, empreinte SHA-256, nombre de pages, présence d'une couche texte (pour les PDF), langue, et les métadonnées de la section 2. C'est le registre du chapitre 05.

**Décidez ce que vous n'indexez pas, et notez pourquoi** dans une colonne `excluded_reason` : les doublons exacts (même empreinte : on n'en garde qu'un), les données personnelles, les modèles vierges, les fichiers de bruit. Ne supprimez rien du corpus : excluez dans le registre.

Tag : `v0.1-inventaire`, à la fin de la section 2.

## 2. Les métadonnées

Aucun fichier ne vous les donne : extrayez-les du chemin, du nom de fichier et du contenu.

| Métadonnée      | D'où la tirer                                                                                                                               |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| Département      | Le premier dossier (`01_Finance`, `03_Production`…)                                                                                     |
| Type de document  | Le dossier et le nom du fichier (PV de CODIR, PV de CA, COPIL, facture, non-conformité, offre de prix…)                                    |
| Date              | Le nom du fichier, et sinon le contenu (« Séance du lundi 13 octobre 2025 »)                                                              |
| Version et statut | `v1`, `v2`, `projet`, `Projet PV`, `copie`, `Copie de`, `(1)`, `FINAL`, les dossiers `Archives`, `Doublons`, `Modeles` |
| Langue            | Détectée par chunk (chapitre 05)                                                                                                           |
| Type de source    | Texte, tableau, image, scan                                                                                                                  |

Les conventions de nommage ne sont pas homogènes, comme dans une vraie entreprise :

| Série                        | Exemple                                                                                   |
| ----------------------------- | ----------------------------------------------------------------------------------------- |
| CODIR 2025                    | `PV_CODIR_2025-10-13.docx`, `PV_CODIR_2025-11-17_v2.docx`                             |
| CODIR 2026                    | `2026-01-12 CODIR PV.docx`, `2026-01-14 CODIR extraordinaire PV.docx`                 |
| CA                            | `PV CA 2025-11-18 signé.pdf`, `Projet PV CA 2026-02-17 v1.docx`                      |
| COPIL ERP                     | `COPIL_Atlas_05_20260205.docx`                                                          |
| Comité de sécurité de Gand | `Verslag Comite PBW Gent 2026-01-22.docx`                                               |
| Reporting, production         | `Reporting 2026-03.xlsx` (un mois, pas un jour), `Productierapport Gent 2026-01.xlsx` |
| Notes de service              | `2026-01-05 NS-2026-01 Gel des recrutements des fonctions support.docx`                 |
| Factures, bons de livraison   | `2026-01-08 Tolerie Mosane TM-2026-0042.jpg`                                            |
| Photos                        | `IMG_20260311_Presse_plieuse.jpg` (date de la photo)                                    |
| Sans date                     | `NC-2025-047.docx`, `REC-2026-017 Comptable fournisseurs.html`, `Tarif 2026.xlsx`   |

Mettez ces métadonnées dans le payload des chunks, avec un *payload index* pour celles que vous filtrerez. Et, comme la ligne patient de l'hôpital, ajoutez en tête de chaque chunk une **ligne de contexte** : « [PV du CODIR du 13 octobre 2025 · 00_Direction/CODIR/2025] ». Un chunk du tableau de suivi des actions qui ne dit pas de quelle séance il vient est inutilisable.

Mesurez l'effet de la ligne de contexte (avec et sans) sur le jeu de développement.

## 3. Une version de référence

Indexez **les documents qui ont du texte** (DOCX, PDF natifs, HTML, PPTX, Markdown, CSV, et les classeurs tels que Docling les convertit), avec la meilleure configuration de l'exercice 3 et la ligne de contexte. Les images et les scans ne sont pas encore lus.

Évaluez tout le jeu de développement et regardez les résultats **par type de question**. Les questions `image_only`, `scan_ocr` et `image_in_document` doivent échouer : c'est le point de départ.

Tag : `v0.2-baseline`.

## 4. Les langues

Notebook, partie 1. Au minimum :

- la langue de chaque chunk dans le payload, et le stemmer de la recherche lexicale choisi selon cette langue (chapitre 05) ;
- une expérience avec **la traduction de la question** (néerlandais et anglais), fusionnée par RRF ;
- un prompt système qui demande de répondre en français, même quand l'extrait est en néerlandais.

À mesurer : les questions `multilingual`, mais aussi toutes les autres (les traductions ajoutent des candidats), et le temps de réponse.

Tag : `v0.3-langues`.

## 5. Les fichiers Excel

Notebook, partie 2. Remplacez la conversion des classeurs par Docling par votre propre lecture :

- `openpyxl` avec `data_only=True`, un passage sur chaque onglet ;
- retrouver les tableaux (titre, en-tête, lignes, notes) ;
- une phrase par ligne avec son contexte (fichier, onglet, titre du tableau, période), les pourcentages et les dates affichés comme dans Excel ;
- pour les grands tableaux, des paquets de lignes avec l'en-tête répété et un chunk de résumé ;
- dans le payload : fichier, onglet, numéro de ligne, période, version.

Pour les questions `excel_reasoning`, comparez deux approches : le RAG seul, et un calcul dans le code (polars ou SQL), choisi par le LLM parmi quelques fonctions que vous écrivez.

À mesurer : `excel_lookup`, `excel_reasoning`, et les pièges du budget et du tarif (`version_trap`).

Tag : `v0.4-excel`.

## 6. Les images et les scans

Notebook, partie 3. Au minimum :

- servir le VLM avec llama-server sur le port 8003 ;
- transcrire toutes les images et toutes les pages des PDF scannés, **une seule fois**, avec un cache ; enregistrer le temps de chaque transcription ;
- lire les graphiques des deux PDF qui en contiennent ;
- construire les chunks : ligne de contexte (titre, dossier, date), transcription, et dans le payload le **chemin de l'image** et la page ;
- **vérifier à la main dix transcriptions** de types différents : combien de nombres ou de noms sont faux ? Notez-le dans le rapport.

Pour les scans, comparez le VLM et l'OCR de Docling sur les questions `scan_ocr` : qualité et temps.

À mesurer : `image_only`, `scan_ocr`, `image_in_document`, et le temps total de lecture des images.

**Bonus : afficher l'image dans le chat.** Quand la réponse s'appuie sur une image ou une page scannée, l'interface affiche l'image sous la réponse (notebook, section 3.9). Mieux : seulement les images des extraits que la réponse cite.

Tag : `v0.5-images`.

## 7. Le temps et les versions

C'est la partie la plus difficile, et celle qui fait le plus de différence. Il faut trouver la bonne version d'une information qui a changé, et ne pas se laisser tromper par les brouillons, les doublons et les rappels.

Pistes, à combiner et à mesurer une par une :

| Piste                              | Idée                                                                                                                                                                                                                                                  |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Statut dans le registre            | Exclure par défaut les brouillons, les doublons et les fichiers de bruit (filtre `must_not` dans Qdrant). Garder les versions anciennes, mais marquées (`valid_from`, `valid_to`, chapitre 05)                                                 |
| Date de référence de la question | Un LLM extrait de la question une date de référence (« en décembre 2025 » → 31/12/2025 ; rien → la date la plus récente). Le code applique un filtre `date <= date de référence` (exercice 3, section 6 : le LLM extrait, le code décide) |
| Ordre chronologique dans le prompt | Envoyer les chunks retenus triés par date, chacun avec sa date                                                                                                                                                                                        |
| Consignes au LLM                   | « Si des extraits se contredisent, la décision la plus récente prime. Un projet de PV ne fait pas foi. Un PV approuvé avec une correction prime sur le PV corrigé. Indique la date de la décision. »                                            |
| Plus de candidats sur un fil       | Pour une question sur un fil de décision, prendre plus de chunks avant le reranking, pour avoir tous les épisodes                                                                                                                                    |
| Données structurées              | Extraire les tableaux de décisions et de suivi des actions des PV du CODIR dans PostgreSQL (numéro, texte, responsable, échéance, statut, date de séance) et répondre aux questions `action_tracking` en SQL                                   |

À mesurer : `decision_current`, `decision_history`, `board_resolution`, `version_trap`, `action_tracking`, et surtout **le taux de pièges** (`trap_hit`) avant et après.

Tag : `v0.6-versions`.

## 8. Évaluation finale

1. Choisissez la meilleure configuration sur le jeu de développement : qualité, mais aussi temps de réponse et coût de l'indexation.
2. Évaluez-la **une seule fois** sur la réserve de 31 questions.
3. Exportez les résultats de PostgreSQL dans `results/` (CSV, commités).

Tag : `v1.0`.

## D'autres pistes

Si vous avez du temps, choisissez-en une ou plusieurs :

| Piste                                | Idée                                                                                                                                                             | Questions à surveiller                  |
| ------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| Routage des questions                | Un LLM classe la question (texte, calcul, action du CODIR) et choisit le chemin                                                                                   | `excel_reasoning`, `action_tracking` |
| Parent-child                         | Chercher avec de petits chunks, envoyer au LLM le point entier de l'ordre du jour                                                                                 | `decision_reason`, `meeting_detail`  |
| Décomposer la question              | Une recherche par sous-question pour les questions qui demandent plusieurs faits                                                                                  | `multi_doc`                            |
| Contextual retrieval                 | Un LLM écrit une phrase de contexte pour chaque chunk avant l'embedding                                                                                          | Toutes                                   |
| Seuil du reranker                    | « Je ne sais pas » si le meilleur score est trop bas                                                                                                            | `out_of_corpus`                        |
| Recherche directement sur les images | Le principe de ColPali : chercher sur des embeddings de l'image des pages plutôt que sur leur transcription. À présenter comme une étude, pas à implémenter | `image_only`, `scan_ocr`             |

---

## Livrables

- **Le dépôt GitHub**, avec les tags des étapes et un `README.md` qui permet au formateur de tout relancer :
  1. cloner le dépôt ;
  2. placer le corpus dans `data/` ;
  3. lancer `uv sync` et `docker compose up -d` ;
  4. démarrer les services ;
  5. lancer l'ingestion, puis une expérience.
- **La base PostgreSQL remplie** et son export dans `results/` : la version de référence et au moins une expérience par section 4 à 7.
- **Un `RAPPORT.md`** qui contient :
  - le tableau comparatif des expériences, avec le commit de chacune ;
  - les résultats par type de question et par format de document ;
  - le taux de pièges, avant et après la section 7 ;
  - la lecture des images : le temps total et le taux d'erreur mesuré sur dix transcriptions ;
  - ce qui n'a rien changé, ou a dégradé les résultats ;
  - les résultats sur la réserve de test, comparés au jeu de développement ;
  - trois questions ratées par la meilleure configuration, analysées : où se situe l'échec (inventaire, conversion, chunking, recherche, reranking, génération) et quelle piste pourrait le corriger.
- **Une démonstration** de cinq minutes : trois questions posées en direct, dont une dont la réponse vient d'une image.

## Ce qui sera regardé

- L'historique Git : des commits réguliers et lisibles, les tags, aucun secret dans le dépôt.
- La structure du code : la logique dans `src/`, rien en dur, des expériences reproductibles.
- La rigueur de l'évaluation : une référence, un changement à la fois, la réserve de test respectée.
- Le traitement des pièges : ceux que votre système déjoue, et l'analyse honnête de ceux qu'il ne déjoue pas.
- La qualité du rapport : des chiffres, des explications, des limites.
