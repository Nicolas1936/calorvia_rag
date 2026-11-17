"""Métadonnées d'un document (section 2) : département, type, date, version, statut, type de source.

Tout est déduit du chemin, du nom de fichier et, pour la date, du début du contenu.
Les fonctions sont pures (pas d'accès disque, pas de base) : faciles à tester une par une.

Usage dans l'inventaire :
    meta = extract_metadata(relative_path, text, file_format, pdf_kind, table_count)
"""
from datetime import date
from pathlib import PurePosixPath

import re


# --- Constantes ----------------------------------------------------------------

IMAGE_FORMATS = {'jpg', 'jpeg', 'png'}
TABLE_FORMATS = {'xlsx', 'csv'}

# Noms de mois en français et en néerlandais -> numéro
MONTHS = {
    'janvier': 1, 'février': 2, 'fevrier': 2, 'mars': 3, 'avril': 4, 'mai': 5, 'juin': 6,
    'juillet': 7, 'août': 8, 'aout': 8, 'septembre': 9, 'octobre': 10, 'novembre': 11,
    'décembre': 12, 'decembre': 12,
    'januari': 1, 'februari': 2, 'maart': 3, 'april': 4, 'mei': 5, 'juni': 6, 'juli': 7,
    'augustus': 8, 'oktober': 10, 'december': 12,
}
MONTH_NAMES = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet',
               'août', 'septembre', 'octobre', 'novembre', 'décembre']

# Numéros d'identifiant à ignorer pour la date : NC-2025-047, CAPEX-2025-014, REC-2026-017, TM-2026-0042
IDS = re.compile(r'\b[A-Z]{2,6}-\d{2,4}-\d{2,5}\b')

# Libellés qui annoncent LA date du document (pas une date citée plus loin)
LABELS = (r"(?:séance du|réunion du|date d['’]ouverture|date de la réunion|date de la demande|date d['’]application"
          r"|publiée? le|révision \w+ du|vergadering van|stand van zaken|gepubliceerd op|datum|date)")
WEEKDAY = r'(?:lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche|maandag|dinsdag|woensdag|donderdag|vrijdag)?\s*'

# Type de document : (motif cherché dans « chemin/nom » en minuscules, type). Le premier qui correspond gagne.
DOC_TYPES = [
    (r'00_direction/modeles/',                    'modele'),
    (r'codir/annexes/',                           'annexe_codir'),
    (r'/codir/|pv_codir|codir pv',                'pv_codir'),
    (r'convocation ca',                           'convocation_ca'),
    (r'\bpv ca\b',                                'pv_ca'),
    (r'\bpv ago\b',                               'pv_ag'),
    (r'copil',                                    'copil'),
    (r'comite pbw|/cppt/',                        'comite_securite'),
    (r'\bns-\d{4}',                               'note_de_service'),
    (r'\bnc-\d{4}',                               'non_conformite'),
    (r'factures_fournisseurs/',                   'facture'),
    (r'bons_de_livraison/',                       'bon_de_livraison'),
    (r'\bdv-\d{4}',                               'offre_de_prix'),
    (r'ligne_l4/offre ',                          'offre_fournisseur'),
    (r'\brec-\d{4}',                              'offre_emploi'),
    (r'\bint-\d{4}',                              'fiche_intervention'),
    (r'\bcapex-\d{4}',                            'demande_capex'),
    (r'reporting \d{4}-\d\d',                     'reporting_mensuel'),
    (r'commentaires de gestion',                  'commentaires_gestion'),
    (r'productierapport|rapport production',      'rapport_production'),
    (r'/newsletter/',                             'newsletter'),
    (r'communiques_presse/',                      'communique'),
    (r'/intranet/',                               'page_intranet'),
    (r'fiches_produits/',                         'fiche_produit'),
    (r'\bimg_\d{8}',                              'photo'),
    (r'organigramme',                             'organigramme'),
    (r'\bphoto\b',                                'photo'),
    (r'tableaux_de_bord/',                        'tableau_de_bord'),
    (r'/indicateurs/',                            'indicateur'),
    (r'appel_offres_erp/',                        'appel_offres'),
    (r'/courriers/|/reclamations/courrier|lettre|terugroepbrief', 'courrier'),
    (r'registre',                                 'registre'),
    (r'\bfaq\b',                                  'faq'),
    (r'actieplan|plan d.action',                  'plan_action'),
    (r'\bplanning\b|\bplan\b|plattegrond|\bschema\b|feuille de route', 'plan_schema'),
    (r'budget',                                   'budget'),
    (r'tarif',                                    'tarif'),
    (r'politique|charte|reglement',               'politique'),
    (r'procedures/|procedure |\bmo-|\bwi-',       'procedure'),
    (r'contrats/|supply agreement|contract',      'contrat'),
    (r'cr reunion',                               'compte_rendu'),
    (r'rapport|verslag|incidentrapport|bilan|synthese|resultats', 'rapport'),
    (r'presentation',                             'presentation'),
    (r'effectifs|enquete|suivi|prevision|export|liste|evaluation|grille', 'tableau_suivi'),
]

# Libellé lisible de chaque type, pour la ligne de contexte
TYPE_LABELS = {
    'pv_codir': 'PV du CODIR', 'annexe_codir': 'Annexe du CODIR', 'pv_ca': 'PV du CA',
    'convocation_ca': 'Convocation du CA', 'pv_ag': "PV de l'assemblée générale", 'copil': 'COPIL Atlas',
    'comite_securite': 'Comité de sécurité', 'note_de_service': 'Note de service',
    'non_conformite': 'Fiche de non-conformité', 'facture': 'Facture fournisseur',
    'bon_de_livraison': 'Bon de livraison', 'offre_de_prix': 'Offre de prix',
    'offre_fournisseur': 'Offre fournisseur', 'offre_emploi': "Offre d'emploi",
    'fiche_intervention': "Fiche d'intervention", 'demande_capex': 'Demande capex',
    'reporting_mensuel': 'Reporting mensuel', 'commentaires_gestion': 'Commentaires de gestion',
    'rapport_production': 'Rapport de production', 'newsletter': 'Newsletter Calorvia Info',
    'communique': 'Communiqué de presse', 'photo': 'Photo', 'organigramme': 'Organigramme',
    'compte_rendu': 'Compte rendu', 'budget': 'Budget', 'tarif': 'Tarif', 'tableau_de_bord': 'Tableau de bord commercial',
}


# --- Département ----------------------------------------------------------------

def department(relative_path):
    """Premier dossier du chemin : 01_Finance, 03_Production… (None pour un fichier à la racine)."""
    return relative_path.parts[0] if len(relative_path.parts) > 1 else None


# --- Type de document -----------------------------------------------------------

def doc_type(relative_path):
    """Type du document d'après son dossier et son nom ; 'autre' si aucune règle ne correspond."""
    target = '/' + str(relative_path).lower()
    for pattern, kind in DOC_TYPES:
        if re.search(pattern, target):
            return kind
    return 'autre'


# --- Date -----------------------------------------------------------------------

def make_date(year, month = 1, day = 1):
    """Date valide, ou None si elle est impossible (30 février…)."""
    try:
        return date(int(year), int(month), int(day))
    except ValueError:
        return None


def date_from_name(name):
    """(date, précision) tirée du nom de fichier, ou (None, None). Précision : 'day' ou 'month'."""
    name = IDS.sub(' ', name)  # 1. effacer les numéros d'identifiant
    rules = [  # 2. du plus précis au moins précis
        (r'(?<!\d)(20\d\d)-(\d\d)-(\d\d)(?!\d)', lambda y, m, d: (make_date(y, m, d), 'day')),  # 2025-10-13
        (r'(?<!\d)(20\d\d)(\d\d)(\d\d)(?!\d)',   lambda y, m, d: (make_date(y, m, d), 'day')),  # 20260205
        (r'(?<!\d)(\d\d)-(\d\d)-(20\d\d)(?!\d)', lambda d, m, y: (make_date(y, m, d), 'day')),  # 16-12-2025
        (r'(?<!\d)(20\d\d)-(\d\d)(?![\d-])',     lambda y, m: (make_date(y, m), 'month')),      # 2026-03
        (rf"({'|'.join(MONTHS)})\s+(20\d\d)",
         lambda m, y: (make_date(y, MONTHS[m.lower()]), 'month')),                                # decembre 2025
    ]
    for pattern, build in rules:
        if match := re.search(pattern, name):
            found, precision = build(*match.groups())
            if found:
                return found, precision
    return None, None


def period_from_name(name):
    """Année ou période de validité (« Tarif 2026 », « Plan 2026-2028 ») : ce n'est pas une date de document."""
    name = IDS.sub(' ', name)
    if match := re.search(r'(?<![\d-])(20\d\d)-(20\d\d)(?![\d-])', name):  # 2026-2028
        return f'{match.group(1)}-{match.group(2)}'
    if match := re.search(r'(?<![\d-])(20\d\d)(?![\d-])', name):           # 2026 seul
        return match.group(1)
    return None


def _search_date(pattern, text):
    """Première date « jour mois-en-lettres année » ou « jj/mm/aaaa » qui suit `pattern` dans `text`."""
    month_names = '|'.join(MONTHS)
    in_letters = rf'{pattern}{WEEKDAY}(\d{{1,2}})(?:er)?\s+({month_names})\s+(20\d\d)'
    in_digits = rf'{pattern}(\d{{1,2}})/(\d{{1,2}})/(20\d\d)'
    for regex, letters in ((in_letters, True), (in_digits, False)):
        if match := re.search(regex, text, re.IGNORECASE):
            day, month, year = match.groups()
            if found := make_date(year, MONTHS[month.lower()] if letters else month, day):
                return found
    return None


def date_from_text(text):
    """(date, 'day') trouvée en haut du contenu, ou (None, None).

    1. une date après un libellé (« Séance du lundi 17 novembre 2025 », « | Date d'ouverture | 02/12/2025 | »)
       dans les 1 500 premiers caractères ;
    2. sinon, la première date du titre (300 premiers caractères) : « Comité … · Seneffe · 13 janvier 2026 ».
    """
    head = re.sub(r'\s+', ' ', text[:1500])  # retours à la ligne -> espaces
    if found := _search_date(rf'{LABELS}[\s:|]*', head):
        return found, 'day'
    if found := _search_date(r'(?<![\d/])', head[:300]):
        return found, 'day'
    return None, None


def doc_date(name, text = ''):
    """Date du document : le nom d'abord, le contenu si le nom ne donne pas de jour."""
    found, precision = date_from_name(name)
    if precision == 'day':
        return found, precision
    from_text = date_from_text(text)
    if from_text[0]:
        return from_text
    return found, precision  # mois tiré du nom, ou rien


# --- Version et statut ----------------------------------------------------------

def version_status(relative_path):
    """(version, statut) d'après le nom et les dossiers. « FINAL » est volontairement ignoré (piège du corpus)."""
    name = relative_path.stem.lower()
    folders = str(relative_path.parent).lower()
    # v1, v2… même collé par un « _ » (PV_CODIR_2025-11-17_v2) ; « _ » compte comme une lettre pour \b
    version = int(match.group(1)) if (match := re.search(r'(?<![a-z0-9])v(\d+)(?![a-z0-9])', name)) else None

    if 'doublons' in folders or re.search(r'\bcopie\b|\(\d\)', name):
        status = 'copie'
    elif 'modeles' in folders:
        status = 'modele'
    elif 'archives' in folders:
        status = 'archive'
    elif re.search(r'^projet\b|- projet\b|\bprojet v\d', name) or 'projets_pv' in folders:
        status = 'projet'
    elif 'signé' in name or 'signe' in name.split() or 'pv_signes' in folders or 'approuvee' in name:
        status = 'valide'
    else:
        status = None
    return version, status


# --- Type de source -------------------------------------------------------------

def source_type(file_format, pdf_kind = None, table_count = 0):
    """texte, texte + tableau, texte + images, tableau, image ou scan."""
    if file_format in IMAGE_FORMATS:
        return 'image'
    if pdf_kind == 'scan':
        return 'scan'
    if file_format in TABLE_FORMATS:
        return 'tableau'
    if pdf_kind == 'texte + images':
        return 'texte + images'
    return 'texte + tableau' if table_count else 'texte'


# --- Ligne de contexte ----------------------------------------------------------

def format_date(value, precision):
    """Date en toutes lettres, comme dans les questions : « du 17 novembre 2025 », « de mars 2026 »."""
    if value is None:
        return None
    if precision == 'day':
        day = '1er' if value.day == 1 else value.day
        return f'du {day} {MONTH_NAMES[value.month - 1]} {value.year}'
    return f'de {MONTH_NAMES[value.month - 1]} {value.year}'


def context_line(meta, relative_path):
    """« [PV du CODIR du 17 novembre 2025 (v2) · 00_Direction/CODIR/2025] », à mettre en tête de chaque chunk."""
    label = TYPE_LABELS.get(meta['doc_type'])
    if label is None:  # type sans libellé : on reprend le nom du fichier
        parts = [relative_path.stem]
        if date_from_name(relative_path.stem)[0] is None:  # date trouvée dans le contenu : on l'ajoute
            parts.append(format_date(meta['doc_date'], meta['date_precision']))
        return f"[{' '.join(part for part in parts if part)} · {relative_path.parent}]"

    if meta['status'] == 'projet':  # « Projet de PV du CA », « Projet de tarif »
        label = f'Projet de {label if label[:2].isupper() else label[0].lower() + label[1:]}'
    identifier = IDS.search(relative_path.stem)  # NC-2025-047, NS-2026-01, TM-2026-0042…
    parts = [
        label,
        identifier.group() if identifier else None,
        meta['period'],
        format_date(meta['doc_date'], meta['date_precision']),
        f"(v{meta['version']})" if meta['version'] else None,
    ]
    return f"[{' '.join(part for part in parts if part)} · {relative_path.parent}]"


# --- Point d'entrée -------------------------------------------------------------

def extract_metadata(relative_path, text = '', file_format = None, pdf_kind = None, table_count = 0):
    """Toutes les métadonnées d'un document : le dictionnaire s'ajoute à la ligne de l'inventaire."""
    relative_path = PurePosixPath(relative_path)
    file_format = file_format or relative_path.suffix.lower().lstrip('.')
    doc_date_value, date_precision = doc_date(relative_path.name, text)
    version, status = version_status(relative_path)
    meta = {
        'department': department(relative_path),
        'doc_type': doc_type(relative_path),
        'doc_date': doc_date_value,
        'date_precision': date_precision,
        'period': period_from_name(relative_path.name),
        'version': version,
        'status': status,
        'source_type': source_type(file_format, pdf_kind, table_count),
    }
    meta['context_line'] = context_line(meta, relative_path)
    return meta
