# Dataset du laboratoire : Calorvia SA

Ce dataset sert au laboratoire de fin de module. Il est volontairement plus proche d'un vrai disque partagé d'entreprise que le corpus de l'hôpital : il y a plus de formats, plus de versions, des scans et des images, et surtout des décisions qui évoluent de semaine en semaine.

Tout est inventé : l'entreprise, les personnes, les fournisseurs, les clients et les chiffres.

## 1. L'entreprise

**Calorvia SA** est un fabricant belge de pompes à chaleur (gamme Aéris) et de groupes de ventilation double flux (gamme Ventis). L'entreprise compte environ 620 personnes et a réalisé 148,2 M€ de chiffre d'affaires en 2025.

| Site    | Rôle                                                               | Langue des documents |
| ------- | ------------------------------------------------------------------- | -------------------- |
| Namur   | Siège : direction, finance, RH, informatique, commercial           | français            |
| Seneffe | Usine d'assemblage des pompes à chaleur (lignes L1 à L3, puis L4) | français            |
| Gand    | Usine de ventilation et entrepôt                                   | néerlandais         |
| Lille   | Bureau commercial France                                            | français            |
| Herstal | Entrepôt ouvert en mai 2026                                        | français            |

Le comité de direction (CODIR) réunit huit personnes :

| Personne            | Fonction                                                       |
| ------------------- | -------------------------------------------------------------- |
| Hélène Marchal    | administratrice déléguée (CEO)                              |
| Laurent Dewit       | directeur financier jusqu'au 31 mars 2026                      |
| Sarah Vandamme      | directrice financière ad interim du 1er avril au 14 juin 2026 |
| Isabelle Gérard    | directrice financière depuis le 15 juin 2026                  |
| Thomas Lambert      | directeur des opérations                                      |
| Nadia Benali        | directrice des ressources humaines                             |
| Pierre-Yves Collard | directeur commercial                                           |
| Kevin Mertens       | directeur des systèmes d'information                          |
| Anne Vercammen      | directrice qualité                                            |
| Pieter De Smet      | directeur du site de Gand                                      |

Le conseil d'administration est présidé par Jean-François Delcourt. Caroline Hendrickx en est la secrétaire.

La période couverte va de **septembre 2025 à juin 2026**.

## 2. Le corpus en chiffres

Le corpus contient **393 fichiers** répartis dans 68 dossiers, pour 21 Mo.

| Format      | Fichiers | Ce qu'il faut pour le lire                                                          |
| ----------- | -------- | ----------------------------------------------------------------------------------- |
| DOCX        | 156      | Docling                                                                             |
| PDF natif   | 76       | Docling (2 PDF contiennent des graphiques à lire avec un VLM)                      |
| PDF scanné | 9        | OCR : aucune couche texte                                                           |
| XLSX        | 55       | Docling (plusieurs onglets, formules)                                               |
| HTML        | 31       | Docling (en-têtes et pieds de page d'intranet)                                     |
| JPG         | 31       | VLM : photos de plaques, de tableaux blancs, factures et bons de livraison scannés |
| PNG         | 23       | VLM : organigrammes, plans, graphiques, plannings, schémas                         |
| PPTX        | 9        | Docling                                                                             |
| CSV         | 2        | Docling ou polars                                                                   |
| Markdown    | 1        | Docling                                                                             |

Répartition par langue : 342 documents en français, 44 en néerlandais et 7 en anglais.

```
calorvia/
├── 00_Direction/              75   CODIR (2025, 2026, annexes), conseil d'administration
│                                   (PV signés, projets de PV, convocations, AG), stratégie, modèles
├── 01_Finance/                35   budget 2026 (3 versions), reporting mensuel, investissements,
│                                   factures fournisseurs scannées, trésorerie, procédure IBAN
├── 02_RH/                     42   politiques (versions), notes de service, offres d'emploi,
│                                   formation, effectifs, organigrammes, enquête, confidentiel
├── 03_Production/             68   Seneffe (rapports, ligne L4, CPPT, photos), Gent (maandrapporten,
│                                   veiligheid, comité PBW, foto's), maintenance, procédures, plans
├── 04_Qualite/                30   non-conformités, rappel Aéris 12, audit ISO, réclamations, indicateurs
├── 05_Commercial/             52   tarifs (versions), fiches produits FR/NL/EN, offres de prix,
│                                   comptes clés, courriers, réunions, tableaux de bord, salons
├── 06_Achats/                 15   contrats fournisseurs (EN), appel d'offres ERP, bons de livraison
├── 07_IT/                     31   projet Atlas (COPIL, plannings, documentation), sécurité,
│                                   architecture, support
├── 08_Juridique/               6   bail de Herstal, contrats, RGPD, assurance
├── 09_Communication/          22   newsletters, communiqués de presse FR/NL/EN, pages intranet
├── 10_RSE/                     4   bilan carbone, rapport RSE, graphiques
└── 99_Archives/               13   2024, doublons, fichiers sans intérêt
```

## 3. Les séries de documents

Le cœur du dataset est constitué de documents qui se suivent. Chacun reprend une partie des précédents.

| Série                         | Nombre                    | Format                                             | Contenu                                                                                                                                                                       |
| ------------------------------ | ------------------------- | -------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PV du CODIR                    | 41 séances (42 fichiers) | DOCX                                               | Présents, indicateurs de la semaine, tableau de suivi des actions, points de l'ordre du jour, décisions numérotées (D-25-07), nouvelles actions (A-26-012), tour de table |
| PV du conseil d'administration | 10 séances + 3 projets   | PDF (4 scannés et signés), DOCX pour les projets | Approbation du PV précédent, situation financière, résolutions                                                                                                            |
| COPIL du projet ERP Atlas      | 14                        | DOCX                                               | Météo par chantier, indicateurs, points marquants                                                                                                                           |
| Comité PBW de Gand            | 9                         | DOCX en néerlandais                               | Accidents, absentéisme, suivi des mesures de sécurité                                                                                                                      |
| CPPT de Seneffe                | 3                         | DOCX                                               | Accidents du trimestre                                                                                                                                                        |
| Reporting mensuel              | 9                         | XLSX à 4 ou 5 onglets                             | Synthèse, ventes par gamme et par région, effectifs, commentaires                                                                                                           |
| Rapports de production         | 9 + 9                     | XLSX (Seneffe en français, Gand en néerlandais)  | Production par ligne, arrêts, rebut, TRS                                                                                                                                     |
| Réunions commerciales         | 6                         | DOCX                                               | Ventes du mois par région                                                                                                                                                    |
| Newsletter interne             | 10                        | HTML                                               | Reprend les nouvelles du mois, avec du texte répété dans chaque numéro                                                                                                    |

Le tableau de suivi des actions du CODIR est calculé : une action apparaît « En cours », passe « En retard » si son échéance est dépassée, puis « Clôturée » avec un commentaire. On peut donc suivre une action d'un PV à l'autre.

## 4. Les fils de décision

Dix sujets évoluent au fil des réunions. Ce sont eux qui rendent le dataset difficile : la bonne réponse dépend de la date, et les anciennes valeurs restent présentes dans le corpus.

| Fil                                   | Chronologie                                                                                                                                                                                                                                                             | État final                                                                                 |
| ------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| **ERP (projet Atlas)**          | 08/09/25 consultation lancée ; 13/10 trois éditeurs présélectionnés ; 17/11 Praxio recommandé (82/100) ; 18/11 CA : 680 k€ ; 01/12 mise en production fixée au 1er avril ; 09/02/26 report au 1er juin ; 17/02 CA : surcoût de 45 k€ ; 18/05 go               | En production le 1er juin 2026 (Namur, Seneffe, Lille), le 15 juin à Gand ; budget 725 k€ |
| **Ligne L4 à Seneffe**         | 15/09/25 projet à 1,4 M€ ; 21/10 CA : reporté ; 17/11 version phasée à 1,25 M€ ; 18/11 CA : approuvé (le PV écrit 1,2 M€ par erreur) ; 16/12 correction du PV ; 26/01/26 aide régionale de 30 % (375 k€), commande ; 27/04 livraison retardée de 3 semaines | Présérie le 18 juin, mise en service le 6 juillet 2026                                    |
| **Hausse tarifaire 2026**       | 29/09/25 proposition à 4 % ; 06/10 décision 3,5 % standard / 5 % premium ; 24/10 courrier aux clients ; 19/01/26 exception Distrinergie à 2 %                                                                                                                        | 3,5 % / 5 %, Distrinergie à 2 % contre 2 400 unités                                       |
| **Télétravail**               | Politique v2 (2023) : 1 jour ; 27/10/25 pilote à 2 jours décidé ; 05/01/26 début du pilote ; 13/04 généralisation                                                                                                                                                 | 2 jours depuis le 1er mai 2026, mardi obligatoire, 40 € par mois                           |
| **Accident de chariot à Gand** | 12/11/25 accident (le PV v1 du 17/11 écrit « jeudi 13 ») ; 17/11 vitesse limitée à 8 km/h (avant : 12 km/h) ; 12/01/26 audit, passage à 6 km/h                                                                                                                    | 6 km/h dans les allées, 10 km/h sur les voies principales                                  |
| **Rappel de l'Aéris 12**       | 01/12/25 réclamations ; 08/12 rappel de 214 unités, provision de 180 k€ ; suivi de l'avancement à chaque CODIR ; 02/03/26 Valtek prend en charge 65 %                                                                                                               | Clôturé le 31 mars 2026 : 211 unités réparées, 3 introuvables                          |
| **Cybersécurité**             | 13/01/26 hameçonnage et tentative de fraude à l'IBAN ; 14/01 CODIR extraordinaire, MFA obligatoire au 28/02 ; 23/02 report au 15/03 pour les terminaux partagés                                                                                                      | MFA à 100 % depuis le 13 mars 2026                                                         |
| **Entrepôt de Herstal**        | 05/01/26 saturation de Gand ; 02/02 recommandation ; 17/02 CA : bail approuvé (le projet de PV indique un autre loyer) ; 04/03 signature ; 27/04 retard                                                                                                                | Opérationnel depuis le 18 mai 2026                                                         |
| **Gel des recrutements**        | 15/12/25 proposition ; 16/12 CA : gel au premier trimestre ; 21/04/26 CA : levée                                                                                                                                                                                       | Levé au 1er mai 2026                                                                       |
| **Direction financière**       | 26/01/26 départ annoncé ; 17/02 CA : intérim de Sarah Vandamme ; 19/05 CA : nomination d'Isabelle Gérard (le projet de PV indique le 1er juillet)                                                                                                                   | Isabelle Gérard depuis le 15 juin 2026                                                     |

## 5. Les pièges

| Piège                               | Où le trouver                                                                                                                                                                                 | Ce qu'on observe si le pipeline tombe dedans                     |
| ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| Décisions qui changent              | Fils de décision ci-dessus                                                                                                                                                                    | Le RAG répond avec une date ou une valeur dépassée            |
| Rappels des anciennes valeurs        | « Pour rappel, la mise en production avait été fixée au 1er avril… »                                                                                                                     | Le bon chunk contient aussi la mauvaise valeur                   |
| Erreur corrigée dans le PV suivant  | PV du CA du 18/11/2025 (scanné) : 1,2 M€ au lieu de 1 250 000 €                                                                                                                             | Seul le PV de décembre donne le bon montant                     |
| Brouillon et version finale          | `Projets_PV/` : loyer de 22,80 €/m² au lieu de 23,50 €, entrée en fonction au 1er juillet au lieu du 15 juin                                                                             | Le brouillon est plus proche lexicalement de certaines questions |
| Versions de documents                | Budget v1, v2 et approuvé ; tarif 2026 projet v1 et final ; politique de télétravail v1, v2 et v3 ; procédure MFA v1 et v2 ; organigrammes 2024 à 2026 ; PV du CODIR du 17/11 en v1 et v2 | Mélange de versions dans le contexte                            |
| Nom de fichier trompeur              | `99_Archives/Doublons/Budget 2026 v2 FINAL.xlsx` contient la version 2                                                                                                                       | Le mot « FINAL » attire la recherche                           |
| Doublons                             | Copies dans `Doublons/`, grille ERP en double, PDF et DOCX de la politique v3, rapport 8D en annexe                                                                                          | Les mêmes chunks occupent plusieurs places du top k             |
| Néerlandais et anglais              | Gand, contrats fournisseurs, communiqués                                                                                                                                                      | Questions en français, réponse dans une autre langue           |
| Scans sans couche texte              | 4 PV de CA signés, avenant Distrinergie, attestation d'assurance, courriers clients, fichier `scan0001.pdf`                                                                                 | Le document est vide sans OCR                                    |
| Information seulement dans une image | Organigrammes (rattachements), plaques signalétiques, plans, tableaux blancs, Gantt, schémas, factures                                                                                       | Le document est vide sans VLM                                    |
| Graphique dans un PDF                | Annexe de l'enquête télétravail, rapport RSE                                                                                                                                                | Le texte du PDF ne contient pas les valeurs                      |
| Excel tel que Docling le lit         | Pourcentages en décimal (`0.035`), lignes de titre fusionnées répétées dans chaque colonne, nom de l'onglet perdu                                                                       | Les nombres ne ressemblent pas à ceux des PV                    |
| Contenu répété                    | Pieds de page, en-têtes d'intranet, rubriques fixes des newsletters, paragraphe « À propos » des communiqués                                                                              | Chunks presque identiques                                        |
| Données personnelles                | `02_RH/Confidentiel/Entretiens annuels 2025 - synthese.xlsx`                                                                                                                                 | À exclure de l'index ou à protéger par un filtre              |
| Fichiers sans intérêt              | Modèles vierges, `Nouveau document Microsoft Word.docx`, `test.xlsx`, `scan0001.pdf`                                                                                                    | Bruit dans l'index                                               |

## 6. Le jeu d'évaluation

`calorvia_eval.json` contient **158 questions**, au même format que le golden dataset de l'hôpital. Le code d'évaluation du chapitre 04 fonctionne donc sans modification.

| Type                  | Nombre | Ce qu'il teste                                                                                    |
| --------------------- | ------ | ------------------------------------------------------------------------------------------------- |
| `decision_current`  | 15     | L'état actuel d'une décision qui a changé                                                      |
| `decision_history`  | 10     | L'état d'une décision à une date passée                                                       |
| `decision_reason`   | 8      | La raison d'une décision                                                                         |
| `action_tracking`   | 12     | Responsable, échéance et statut d'une action du CODIR                                           |
| `meeting_detail`    | 10     | Présence, présidence, indicateur d'une séance précise                                         |
| `board_resolution`  | 8      | Résolutions du conseil, dont la correction du PV                                                 |
| `excel_lookup`      | 16     | Une valeur dans un onglet Excel                                                                   |
| `excel_reasoning`   | 6      | Comparer ou repérer un maximum dans un tableau                                                   |
| `image_only`        | 15     | Une information présente uniquement dans une image                                               |
| `image_in_document` | 2      | Une valeur lisible uniquement dans un graphique intégré à un PDF                               |
| `scan_ocr`          | 8      | Un scan ou une photo de document                                                                  |
| `multilingual`      | 10     | Question en français, réponse dans un document néerlandais ou anglais                          |
| `version_trap`      | 6      | Choisir la bonne version d'un document (au total, 21 questions de tous types listent des pièges) |
| `multi_doc`         | 8      | Combiner des informations de plusieurs documents                                                  |
| `factual`           | 18     | Un fait simple dans un document                                                                   |
| `out_of_corpus`     | 6      | L'information n'existe pas : le RAG doit dire qu'il ne sait pas                                   |

Niveau de difficulté indiqué dans chaque question : 59 faciles, 81 moyennes, 18 difficiles. 44 questions ont au moins une preuve dans une image ou un scan.

Exemple de question avec un piège :

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

| Champ                    | Contenu                                                                                                                                                                                                                      |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`                   | Identifiant de la question                                                                                                                                                                                                   |
| `type`                 | Type de question (tableau ci-dessus)                                                                                                                                                                                         |
| `thread`               | Fil de décision concerné (`erp`, `l4`, `price`, `telework`, `accident`, `recall`, `cyber`, `herstal`, `freeze`, `cfo`…) ou `null`                                                                   |
| `question`, `answer` | Question et réponse attendue, en français                                                                                                                                                                                  |
| `evidence`             | Comme pour l'hôpital : un chunk correspond à une entrée s'il vient du `document` et contient tous les `snippets`. `grade` 2 = contient la réponse, 1 = contexte utile ; il faut couvrir chaque `fact` différent |
| `traps`                | **Nouveau.** Chunks qui contiennent une réponse fausse ou dépassée : brouillon, ancienne version, PV corrigé ensuite. 21 questions en ont                                                                          |
| `difficulty`           | `facile`, `moyen` ou `difficile`                                                                                                                                                                                       |
| `notes`                | Explication du piège, pour l'analyse des erreurs                                                                                                                                                                            |

Le champ `traps` permet une mesure de plus que pour l'hôpital : la part des questions pour lesquelles un piège remonte dans le top k, et la part des réponses qui reprennent la valeur du piège.

Pour les images et les scans, les extraits de preuve (`snippets`) sont volontairement courts : un numéro de série, un nom, un nombre. La description produite par un VLM ou le texte d'un OCR ne reprend pas toujours la mise en forme exacte de l'image. Pour ces questions, la note du juge (chapitre 04) compte plus que le rappel calculé sur les extraits.

## 7. Comment les preuves ont été vérifiées

Le générateur refuse de produire le dataset si une seule preuve est introuvable :

- DOCX, XLSX, PPTX, HTML, Markdown et CSV sont convertis avec Docling, comme dans le cours, et chaque extrait est recherché dans le résultat ;
- pour les PDF natifs, chaque extrait est recherché dans la couche texte ;
- pour les scans et les images, l'extrait doit faire partie du texte dessiné par le générateur. En plus, un OCR (Tesseract) contrôle qu'il est lisible. Sur les 68 extraits concernés, Tesseract en lit 66. Les 2 autres sont des difficultés voulues pour le VLM : un « 1120 °C » flou sur une plaque et une annotation manuscrite ;
- aucune formule Excel ne doit être en erreur. Les valeurs des formules sont calculées par LibreOffice, comme Excel le ferait à l'enregistrement : sans cela, Docling lirait des cellules vides.

## 8. Fichiers fournis

| Fichier                    | Pour qui   | Contenu                                                                                                                                                                                                                                                                        |
| -------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `calorvia_dataset.zip`   | Étudiants | `corpus/calorvia/` (les 393 fichiers) et `corpus/calorvia_eval.json`                                                                                                                                                                                                       |
| `calorvia_formateur.zip` | Formateur  | Le générateur (`generate_lab_corpus.py` et le module `calorvia/`) et `calorvia_documents.json`, une fiche par document : famille, statut (final, brouillon, obsolète, doublon, bruit), version, langue, données personnelles, besoin d'un VLM, notes sur les pièges |

`calorvia_documents.json` révèle les pièges : il ne faut pas le donner aux étudiants.

Pour régénérer le dataset à l'identique (graine fixe) :

```bash
uv add python-docx openpyxl python-pptx reportlab pymupdf pillow matplotlib numpy "docling>=2.94"
# LibreOffice et Graphviz doivent être installés ; Tesseract est facultatif (contrôle OCR)
uv run python generate_lab_corpus.py --output ../corpus
```

La génération et la vérification prennent environ 2 minutes 30. Les polices manuscrites des tableaux blancs et des annotations (Caveat, Kalam, Patrick Hand) sont livrées dans `calorvia/fonts/`, sous licence SIL Open Font License.
