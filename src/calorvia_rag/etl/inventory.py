"""Inventaire du corpus : une ligne par fichier dans la table `documents` (le registre du chapitre 05).

Même approche que le notebook de pistes (parties 1.1 et 3.1) : PyMuPDF pour la couche texte des PDF,
Docling pour les autres formats, py3langid pour la langue.

Rien n'est supprimé du corpus : les fichiers à ne pas indexer restent dans le
registre, avec une raison dans `excluded_reason`.

Usage : uv run python -m calorvia_rag.etl.inventory
"""
from calorvia_rag.config import settings
from calorvia_rag.db import save_inventory
from calorvia_rag.etl.metadata import extract_metadata

from collections import defaultdict
from functools import cache
from pathlib import Path, PurePosixPath
from time import perf_counter

import hashlib
import re

import pymupdf
from docling.document_converter import DocumentConverter
from py3langid.langid import MODEL_FILE, LanguageIdentifier


# --- Configuration -----------------------------------------------------------

# Dossiers jamais indexés, et pourquoi. Chemins relatifs à la racine du corpus.
EXCLUDED_FOLDERS = {
    '02_RH/Confidentiel': 'personal_data',
    '00_Direction/Modeles': 'blank_template',
    '99_Archives/Divers': 'noise',
}

# Parmi des doublons, on garde le premier dans cet ordre :
# hors dossier Doublons, hors Archives, chemin le plus court, puis ordre alphabétique.
DUPLICATE_FOLDERS = ('99_Archives/Doublons',)
ARCHIVE_FOLDERS = ('99_Archives',)

TEXT_FORMATS = {'docx', 'pdf', 'html', 'pptx', 'md', 'xlsx', 'csv'}   # lus avec PyMuPDF / Docling
IMAGE_FORMATS = {'jpg', 'jpeg', 'png'}                                # pas de texte ici : lues plus tard par le VLM
LANGUAGES = ['fr', 'nl', 'en', 'de']                                  # seules réponses possibles de la détection
MIN_CONTENT_CHARS = 20                                                # en dessous : pas d'empreinte de contenu


# --- Objets lourds, créés une seule fois -------------------------------------

@cache  # Docling charge des modèles : on crée le convertisseur une fois, réutilisé pour tous les fichiers
def get_converter():
    return DocumentConverter()


@cache  # idem pour le modèle de langue
def get_language_identifier():
    identifier = LanguageIdentifier.from_model_file(MODEL_FILE, norm_probs = True)
    identifier.set_languages(LANGUAGES)  # limite aux langues du corpus
    return identifier


def detect_language(text, default = 'fr', min_probability = 0.9):
    """Langue d'un texte ; `default` si le texte est trop court ou la détection peu fiable (chapitre 05)."""
    if len(text.split()) < 5:  # trop peu de mots pour deviner
        return default
    language, probability = get_language_identifier().classify(text)
    return language if probability >= min_probability else default


# --- Lecture d'un fichier ----------------------------------------------------

def count_pdf_tables(pdf):
    """Nombre de tableaux détectés par PyMuPDF (0 si la détection échoue)."""
    try:
        return sum(len(page.find_tables().tables) for page in pdf)
    except Exception:
        return 0


def pdf_info(path):
    """Nombre de pages, texte, type, tableaux et images d'un PDF. Type : 'scan', 'texte + images' ou 'texte'."""
    with pymupdf.open(path) as pdf:
        text = ' '.join(page.get_text() for page in pdf)          # texte sélectionnable de toutes les pages
        images = sum(len(page.get_images()) for page in pdf)      # nombre d'images intégrées
        tables = count_pdf_tables(pdf) if text.strip() else 0     # pas de tableau lisible dans un scan
        page_count = pdf.page_count
    if not text.strip():  # aucun texte -> les pages sont des photos du papier
        kind = 'scan'
    else:
        kind = 'texte + images' if images else 'texte'
    return page_count, text, kind, tables, images


def docling_info(path):
    """Nombre de pages (slides PPTX, feuilles XLSX ; None sans notion de page), texte brut, tableaux et images."""
    document = get_converter().convert(path).document
    return len(document.pages) or None, document.export_to_text(), len(document.tables), len(document.pictures)


def read_file(path, file_format):
    """Nombre de pages, texte brut, type de PDF, tableaux, images et erreur de lecture d'un fichier."""
    # Renvoie toujours 6 valeurs : (page_count, text, pdf_kind, table_count, image_count, error)
    try:
        if file_format == 'pdf':
            return *pdf_info(path), None
        if file_format in TEXT_FORMATS:
            page_count, text, tables, images = docling_info(path)
            return page_count, text, None, tables, images, None
        if file_format in IMAGE_FORMATS:
            return 1, '', None, 0, 1, None  # 1 « page », texte vide, l'image elle-même
        return None, '', None, 0, 0, f'unsupported format: {file_format}'
    except Exception as error:  # un fichier cassé ne doit pas arrêter tout l'inventaire
        return None, '', None, 0, 0, f'{type(error).__name__}: {error}'


# --- Empreintes --------------------------------------------------------------

def sha256_file(path, block_size = 1 << 20):
    """Empreinte des octets : même valeur = copie exacte du fichier."""
    digest = hashlib.sha256()
    with open(path, 'rb') as f:
        while block := f.read(block_size):  # lit 1 Mo à la fois, jamais tout le fichier en mémoire
            digest.update(block)
    return digest.hexdigest()


def content_hash(text):
    """Empreinte du texte : reconnaît deux copies enregistrées séparément (octets différents, même texte)."""
    normalized = re.sub(r'\s+', ' ', text).strip().lower()  # ignore espaces, retours à la ligne et majuscules
    if len(normalized) < MIN_CONTENT_CHARS:  # les textes vides (images, scans) seraient tous identiques
        return None
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def folder_exclusion(relative_path):
    """Raison d'exclusion si le fichier est dans un dossier exclu, sinon None."""
    for folder, reason in EXCLUDED_FOLDERS.items():
        if relative_path.is_relative_to(folder):
            return reason
    return None


# --- Une ligne du registre ---------------------------------------------------

def inventory_file(path, corpus_folder):
    """Décrit un fichier : le dictionnaire devient une ligne de la table `documents`."""
    relative_path = PurePosixPath(path.relative_to(corpus_folder).as_posix())  # ex. 02_RH/Organigrammes/x.png
    file_format = path.suffix.lower().lstrip('.')                                # '.PDF' -> 'pdf'
    size_bytes = path.stat().st_size

    if size_bytes:
        page_count, text, pdf_kind, table_count, image_count, error = read_file(path, file_format)
    else:  # fichier vide : rien à lire
        page_count, text, pdf_kind, table_count, image_count, error = None, '', None, 0, 0, None

    return {
        'path': str(relative_path),
        'file_name': path.name,
        'format': file_format,
        'size_bytes': size_bytes,
        'sha256': sha256_file(path),
        'content_sha256': content_hash(text),
        'page_count': page_count,
        'has_text_layer': pdf_kind != 'scan' if file_format == 'pdf' and pdf_kind else None,  # PDF uniquement
        'pdf_kind': pdf_kind,
        'words': len(text.split()),
        'language': detect_language(text) if text.strip() else None,  # None = pas de texte à analyser
        'read_error': error,
        'table_count': table_count,
        'image_count': image_count,
        # Métadonnées de la section 2 : department, doc_type, doc_date, date_precision, period,
        # version, status, source_type, context_line
        **extract_metadata(relative_path, text, file_format, pdf_kind, table_count),
        'excluded_reason': folder_exclusion(relative_path) or ('empty_file' if size_bytes == 0 else None),
        'duplicate_of': None,  # rempli plus tard par mark_duplicates
    }


# --- Doublons (il faut toutes les lignes) ------------------------------------

def keep_order(row):
    """Clé de tri : la plus petite valeur est la copie gardée (False passe avant True)."""
    path = PurePosixPath(row['path'])
    return (
        any(path.is_relative_to(folder) for folder in DUPLICATE_FOLDERS),  # 1. hors Doublons
        any(path.is_relative_to(folder) for folder in ARCHIVE_FOLDERS),    # 2. hors Archives
        len(row['path']),                                                  # 3. chemin le plus court
        row['path'],                                                       # 4. ordre alphabétique
    )


def mark_duplicates(rows, key, reason):
    """Copies qui partagent `key` : on en garde une, les autres sont exclues et pointent vers la copie gardée."""
    # Regroupe par empreinte les lignes encore indexées
    by_key = defaultdict(list)
    for row in rows:
        if row['excluded_reason'] is None and row[key] is not None:
            by_key[row[key]].append(row)

    # Dans chaque groupe : la première après tri est gardée, les autres exclues
    for copies in by_key.values():
        kept, *others = sorted(copies, key = keep_order)
        for row in others:
            row['excluded_reason'] = reason
            row['duplicate_of'] = kept['path']


# --- Tout le corpus ----------------------------------------------------------

def inventory_corpus(corpus_folder):
    """Parcourt le corpus et renvoie une ligne par fichier, doublons déjà marqués."""
    corpus_folder = Path(corpus_folder)
    # Tous les fichiers de tous les sous-dossiers, sauf les fichiers cachés (.xxx)
    files = sorted(p for p in corpus_folder.rglob('*') if p.is_file() and not p.name.startswith('.'))
    rows = [inventory_file(path, corpus_folder) for path in files]
    mark_duplicates(rows, 'sha256', 'exact_duplicate')            # mêmes octets
    mark_duplicates(rows, 'content_sha256', 'duplicate_content')  # même texte, enregistré séparément
    return rows


# --- Résumé dans la console --------------------------------------------------

def count(rows, key):
    """Nombre de lignes par valeur de `key`, les plus fréquentes d'abord."""
    counts = defaultdict(int)
    for row in rows:
        counts[row[key]] += 1
    return dict(sorted(counts.items(), key = lambda item: -item[1]))


def print_summary(rows, duration_s):
    indexed = [row for row in rows if row['excluded_reason'] is None]
    print(f'{len(rows)} files in {duration_s:.1f} s')
    print('Formats:  ', count(rows, 'format'))
    print('Excluded: ', count([row for row in rows if row['excluded_reason']], 'excluded_reason'))
    print('Languages:', count(indexed, 'language'), '(indexed files; None = no text: images, scans)')
    print('PDF kinds:', count([row for row in indexed if row['pdf_kind']], 'pdf_kind'))
    # PDF qui demanderont de l'OCR ou le VLM
    for row in rows:
        if row['pdf_kind'] in ('scan', 'texte + images'):
            print(f"   {row['pdf_kind']:15} {row['path']}")
    # Fichiers illisibles
    for row in rows:
        if row['read_error']:
            print('Read error:', row['path'], '-', row['read_error'])


def main():
    start = perf_counter()
    rows = inventory_corpus(settings.corpus_folder)  # 1. parcourir le corpus
    save_inventory(rows)                             # 2. écrire les lignes dans PostgreSQL
    print_summary(rows, perf_counter() - start)      # 3. afficher ce qui a été trouvé


if __name__ == '__main__':
    main()
