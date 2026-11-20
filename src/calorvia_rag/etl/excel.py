from openpyxl import load_workbook
from datetime import date, datetime

def display_value(cell):
    """La valeur d'une cellule telle qu'Excel l'affiche (pourcentages, dates, entiers)."""
    value = cell.value
    if value is None:
        return ''
    if isinstance(value, (datetime, date)):
        return value.strftime('%d/%m/%Y')
    if isinstance(value, (int, float)) and '%' in cell.number_format:
        decimals = len(cell.number_format.split('.')[1].rstrip('%')) if '.' in cell.number_format else 0
        return f'{value * 100:.{decimals}f} %'.replace('.', ',')
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)

def is_header(cells):
    """Un en-tête ne contient que du texte : « Satisfaction moyenne | 8.1 » est une ligne de données."""
    return all(isinstance(cell.value, str) for cell in cells)

def sheet_tables(ws):
    """Les blocs d'un onglet : [{'title', 'header', 'rows', 'notes'}].
    header vaut None pour un bloc sans en-tête (libellé : valeur) ou un bloc de texte."""
    tables, title, current = [], None, None
    for row in ws.iter_rows():
        cells = [c for c in row if c.value is not None]
        if not cells:                                   # une ligne vide ferme le tableau en cours
            current = None
            continue
        if len(cells) == 1 and current is None:         # une cellule seule hors tableau : titre ou sous-titre
            title = cells[0].value if title is None else f'{title} · {cells[0].value}'
            continue
        if len(cells) == 1:                             # une cellule seule après un tableau : une note
            current['notes'].append(str(cells[0].value))
            continue
        if current is None:                             # première ligne de plusieurs cellules
            header = [c.value for c in row] if is_header(cells) else None
            current = {'title': title, 'header': header, 'rows': [] if header else [list(row)], 'notes': []}
            tables.append(current)
            title = None
        else:
            current['rows'].append(list(row))
    if title is not None:                               # un titre resté sans tableau (onglet « Commentaires ») : du texte
        tables.append({'title': title, 'header': None, 'rows': [], 'notes': []})
    return tables

MAX_ROWS = 30           # au-delà, le tableau est découpé en paquets de lignes, avec un chunk de résumé
ROWS_PER_CHUNK = 20

def row_text(header, row):
    """Une ligne de tableau en phrase : « colonne : valeur ; … », ou « libellé : valeur » sans en-tête."""
    if header is None:
        values = [display_value(cell) for cell in row if cell.value is not None]
        return f'{values[0]} : ' + ' ; '.join(values[1:])
    return ' ; '.join(f'{name} : {display_value(cell)}'
                      for name, cell in zip(header, row) if name is not None and cell.value is not None)

def table_markdown(header, rows):
    lines = ['| ' + ' | '.join('' if name is None else str(name) for name in header) + ' |', '|' + '---|' * len(header)]
    lines += ['| ' + ' | '.join(display_value(cell) for cell in row) + ' |' for row in rows]
    return '\n'.join(lines)

def table_texts(path, ws, table):
    """Les chunks d'un bloc, avec le numéro de leur première ligne dans l'onglet : (texte, ligne)."""
    context = f'{path.stem} · onglet « {ws.title} »'
    if table['title']:
        context += f" · {table['title']}"
    rows = table['rows']
    if not rows:                                             # bloc de texte : le titre est le contenu
        yield context, None
    elif table['header'] is None or len(rows) <= MAX_ROWS:   # une phrase par ligne
        for row in rows:
            yield f"{context} · {row_text(table['header'], row)}", row[0].row
    else:                                                    # grand tableau : un résumé, puis des paquets de lignes
        columns = ', '.join(str(name) for name in table['header'] if name is not None)
        yield f'{context} : tableau de {len(rows)} lignes. Colonnes : {columns}.', rows[0][0].row
        for start in range(0, len(rows), ROWS_PER_CHUNK):
            part = rows[start:start + ROWS_PER_CHUNK]
            yield (f'{context} · lignes {start + 1} à {start + len(part)}\n'
                   + table_markdown(table['header'], part)), part[0][0].row
    if table['notes']:
        yield f"{context} · Notes : {' '.join(table['notes'])}", None

def workbook_texts(path):
    """Tous les chunks d'un classeur : (texte, intitulé, onglet, ligne)."""
    for ws in load_workbook(path, data_only = True).worksheets:
        for table in sheet_tables(ws):
            headings = f"{ws.title} · {table['title']}" if table['title'] else ws.title
            for text, row_number in table_texts(path, ws, table):
                yield text, headings, ws.title, row_number


if __name__ == '__main__':
    from calorvia_rag.config import settings
    for name in ('Plan de formation 2026.xlsx', 'Enquete teletravail - reponses brutes.xlsx'):
        path = next(settings.corpus_folder.rglob(name))
        for text, headings, sheet, row_number in workbook_texts(path):
            print(f'[{sheet} · ligne {row_number}] {text[:180]}')


