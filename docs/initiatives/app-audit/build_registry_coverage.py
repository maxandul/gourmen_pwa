"""Combine manually assigned review scope with the immutable lexical registry inventory.

Assignments below are audit judgements, not inferred from hit counts. No row is
declared completely reviewed by this script. Regeneration preserves the raw map.
"""
import csv
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent
with (OUT / 'UI_REGISTRY_REVIEW.csv').open(encoding='utf-8-sig', newline='') as f:
    rows = list(csv.DictReader(f))
assert len(rows) == 150 and len({r['id'] for r in rows}) == 150
passes = {n: set() for n in range(1, 151)}
groups = {
    1: [2, 3, *range(59, 63), 71, *range(77, 88), *range(112, 115), 123, 125, 128],
    2: [12, 37, 39, 52, 88, *range(92, 95), 98, 137, 148],
    3: [*range(42, 57), *range(69, 77), *range(89, 92)],
    4: [*range(95, 112), *range(115, 123), 124, 126, 127, *range(129, 137), *range(138, 148), 149, 150],
    5: [*range(13, 30), *range(32, 37), 40, 41, 117, 118],
    6: [1, 4, 5, 6, *range(7, 12), 30, 31, *range(63, 68)],
    7: [38, 57, 58, 68],
}
for passage, numbers in groups.items():
    for n in numbers:
        passes[n].add(passage)
missing = set(range(59, 63)) | set(range(77, 88)) | set(range(112, 115))
discrepant = {2, 3, 71, 125, 128}
unused = {48, 66, 67, 70, 72}
records = []
for row in rows:
    n = int(row['id'][4:])
    status = 'code_path_partially_reviewed' if passes[n] else 'lexical_map_only'
    remaining = 'Einzelne Modifier/Unterelemente und Zustands-/Browserabdeckung nicht pauschal abgeschlossen; genaue Grenzen im verknuepften Durchlauf.'
    if n in missing:
        status = 'documented_component_absent'
        remaining = 'Herkunft/Zielversion der dokumentierten Merch-Komponente klaeren; keine Implementierungs- oder Loeschfreigabe.'
    elif n in discrepant:
        status = 'document_discrepancy_confirmed'
        remaining = 'Konkrete Abweichung im Bericht belegt; restlichen Zeilenvertrag nicht automatisch freigeben.'
    elif n in unused:
        status = 'css_only_candidate'
        remaining = 'CSS vorhanden, keine Template-/V2-JS-Treffer; weitere dynamische Erzeuger vor spaeterer Entfernung ausschliessen.'
    if not passes[n]:
        remaining = 'Eigenstaendiger Detailabgleich dieser Zeile noch ausstehend; Suchkarte allein ist kein Review.'
    records.append([row['id'], row['doc_line'], row['row'].split('|')[1].strip(), status,
                    'UI_REGISTRY_REVIEW.md: Durchlauf ' + ', '.join(map(str, sorted(passes[n])) ) if passes[n] else 'UI_REGISTRY_LOCATIONS.json',
                    remaining])
with (OUT / 'UI_REGISTRY_COVERAGE.csv').open('w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['id', 'doc_line', 'component', 'scope_status', 'evidence', 'remaining'])
    w.writerows(records)
counts = Counter(r[3] for r in records)
print(dict(counts))
print('Only mapped:', [r[0] for r in records if r[3] == 'lexical_map_only'])
