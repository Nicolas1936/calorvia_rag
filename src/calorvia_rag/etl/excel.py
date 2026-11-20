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

if __name__ == '__main__':
    from calorvia_rag.config import settings
    for name in ('Reporting 2026-03.xlsx', 'Plan de formation 2026.xlsx', 'Enquete teletravail - reponses brutes.xlsx'):
        path = next(settings.corpus_folder.rglob(name))
        for ws in load_workbook(path, data_only = True).worksheets:
            for table in sheet_tables(ws):
                print(f"{name} [{ws.title}] titre={table['title']!r} en-tête={table['header']} "
                      f"{len(table['rows'])} lignes, notes={table['notes']}")
