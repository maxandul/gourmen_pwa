"""Manual triage of reverse-search candidates; preserves raw evidence and open cases."""
import csv
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent
with (OUT / 'UI_REGISTRY_REVERSE.csv').open(encoding='utf-8-sig', newline='') as f:
    rows = list(csv.DictReader(f))
groups = [
    ('active_public_style', 'landing-footer landing-hero landing-hitlist-block landing-lead-quote landing-logo landing-next-essen social-link socials',
     'public.css:16-56/70-196/253/487-529; Public-Templates laden public.604da1b3.css und enthalten diese Familien. Hitlist-Block wird per AJAX ersetzt. Kein neuer Viewport-/Drittanbieter-Test.'),
    ('active_shell_style', 'logo-link user-actions user-bar-logo user-section',
     '_user_bar.html:12-83 und layout.css:45-110. Aktive Shell-Familien, gemeinsam mit User-Bar dokumentieren; nicht vier neue unabhaengige Komponenten.'),
    ('active_event_structure', 'billbro-workflow-block events-archive-filter events-archive-panel events-archive-toolbar events-cleanup-intro events-stats-summary-insights events-year-planning-list',
     'Templatefundstelle plus components.css:4170/5071/5300/1870/2305; Archiv-Filter/Panel als JS-Anker events/index.html:844-933. Unterelemente existierender Muster, kein pauschaler Funktionsnachweis.'),
    ('active_shared_style', 'flash-messages page-info page-subtitle table',
     'layout.css:443 und app.js:82; components.css:2353/2362-2406; base.css:265. Templatefundstellen belegen Verwendung. table ist im V2 definiert, nicht allein wegen Namen Bootstrap unterstellen.'),
    ('inline_style_and_hook', 'backup-code member-name',
     'backup_codes.html:30 Inline-Styling, :73/124 Auswahl fuer Kopieren/QR; temp_password.html:42 Inline-Styling. Keine echten Codes gelesen oder Aktionen ausgeloest; QR-Funktion besitzt Platzhalterdarstellung und bleibt fachlich nachzupruefen.'),
    ('semantic_wrapper', 'card-description security-tips',
     'edit_member_enhanced.html:143 Absatz bzw. member/security.html:148 Liste; keine eigene V2-Regel gefunden. Element-/Elternstyling bleibt wirksam, benoetigte Spezialdarstellung nicht daraus ableiten.'),
    ('targeted_followup', 'landing-pagination flash-close text-warning',
     'Gezielte Restpruefung: Public-Paginierungsstyles auch im Event-Archiv ohne erkennbaren Public-CSS-Ladeweg; Flash-Close-Button ohne gefundenen Klickhandler; text-warning ohne eigene V2-Regel. Siehe Registry-Durchlauf 12, keine Loeschfreigabe.'),
    ('active_chart_controller', 'ggl-chart ggl-chart-expand-btn ggl-chart-modal events-stats-chart-expand-btn events-stats-chart-modal',
     'ggl/index.html:174-261 und ggl-season.js:382-437; events/index.html:554/738 und events-monatsessen-stats.js:548ff; components.css:1898-2112. Knotenverschiebung/Rueckkehr fuer Vollbild; A-016 bleibt offen, kein neuer Browserlauf.'),
    ('active_navigation_style', 'dashboard-explore-nav event-detail-nav nav-icon nav-item nav-text events-planning-strip',
     'dashboard/index.html:231 + components.css:5076; events/detail.html:32-50 + base.css:293-301/components.css:4096; _bottom_nav.html + layout.css:328-372. Bedingte Navigation/Planung, nicht verwaist; A-002 bleibt bestehen.'),
    ('active_status_display', 'participation-status',
     'events/detail.html:283-288 bildet Teilnahme/Absage/fehlende Antwort ab; components.css:2554-2581 definiert Varianten. Backend-Semantik separat, keine A-044-Entwarnung.'),
    ('status_display_followup', 'update-status status-text',
     'technical.html:313-314, pwa.js:1181ff: Controller setzt display:block, entfernt hidden aber nicht; base.css hidden-Regel gegenpruefen. Styles in pwa.css nicht im untersuchten Template-Ladeweg. Aktiver Hook mit gezielter Browser-Restpruefung, keine Loeschfreigabe.'),
    ('active_shared_style', 'places-details-header places-details-body places-error places-no-results places-result-main places-result-secondary close-btn',
     'admin/create_event.html und events/edit.html:139-228 erzeugen Places-Markup; components.css:3013-3119 stylt es im global geladenen V2-Bundle. Doppelte Controller siehe A-020; keine neue Browserfreigabe.'),
    ('behaviour_or_state_hook', 'save-details-btn',
     'Beide Event-Templates:190/196ff erzeugen den Button und binden Klickverarbeitung ueber diese Klasse. Styling durch btn; Verhalten beim Refactoring erhalten.'),
    ('legacy_modifier_mismatch', 'btn-success',
     'Beide Event-Templates:190 verwenden btn btn-success. Aktiver V2-Stil heisst btn--success; btn-success nur im alten CSS gefunden, das diese Templates nicht separat laden. Basisbutton vorhanden; visuelle Wirkung nicht neu gemessen.'),
    ('reachable_structure_wrapper', 'form-help',
     'admin/create_event.html:420 kombiniert form-help mit text-muted auf small. Keine eigene V2-Regel gefunden; Hilfetext existiert und nutzt Element-/Utility-Styling. Nicht als ungestylten Gesamtbereich einstufen.'),
    ('reachable_local_style', 'btn-remove form-control form-group price-display remove-group variant-row-content variants-container',
     'member.py:343-435 rendert member/merch/order.html; lokale CSS-Regeln dort:400-521, dynamische Zeilen:180-249. Erreichbarer alter Bestellweg, keine verwaisten Klassen; Konsolidierung statt isolierter Loeschung. Visuelle Kaskade nicht vollstaendig geprueft.'),
    ('reachable_structure_wrapper', 'price-group order-info order-items',
     'member/merch/order.html:79/229 kombiniert price-group mit gestyltem form-group; orders.html:45/70 nutzt info-row/Card-Unterelemente. Routen member.py:435/437-445 rendern beide Vorlagen; eigene CSS-Regel fuer Wrapper nicht erforderlich. Restliche Layoutzustaende offen.'),
    ('already_partly_documented', 'accounting-chart-modal accounting-receipt-upload app-shell-install-banner calendar-subscribe form-row landing-hitlist-filter landing-hitlist-toolbar landing-restaurants landing-restaurants-table tool-strip',
     'UI.md Sektion 5 nennt Elemente/Modifier oder Beispiel; kein komplett fehlender Block. Registry-Durchlaeufe 2-5. Restvarianten separat pruefen.'),
    ('behaviour_or_state_hook', 'is-collapsed js-add-variant js-remove color-select size-select quantity-input price-value variant-row',
     'collapsible-card.js, merch-order.js, merch-order-edit.js bzw. admin/merch/article_form.html:244/260; Verhalten erhalten, CSS-Treffer nicht Voraussetzung. Kein vollstaendiger Lebenszyklustest.'),
    ('utility_or_context_style', 'text-muted text-secondary mt-6 max-400 lead eyebrow status-form',
     'base.css:174; components.css:2299/2320/2349/2400-2406; public.css:134/141. Kleine Hilfs-/Kontextregel statt eigener grosser Komponente; Verwendungspfad nicht pauschal getestet.'),
    ('registry_gap_confirmed', 'chip-select chip-select-wrap rating-chip billbro-guess-ranking-table docs-file-list theme-switch',
     'components.css:3653ff/3597ff/1692ff/6220/4366ff; konkrete Namen nicht in UI.md Registry. Templatebeleg in sample; Beziehungen zu vorhandenen Familien dokumentieren, nicht neue Parallelkomponenten bauen.'),
    ('scanner_artifact', 'cls flash-',
     'hamburg2026.html:1257-1258: JS-Verkettung; _flash_messages.html:23: dynamisches flash-{{ flash_mod }}. Keine eigenstaendige Klasse dieses Namens.'),
]
assignments = {}
for status, names, reason in groups:
    for name in names.split():
        assert name not in assignments
        assignments[name] = (status, reason)
output = []
for row in rows:
    family = row['family']
    if family.startswith('hamburg-'):
        status, reason = ('historical_page_scope',
            'Alle erfassten Fundstellen in events/hamburg2026.html; events.py:453-460 sperrt Route nach Sichtbarkeits-Cutoff. Historischen Seitenumfang separat pruefen; keine Loeschfreigabe oder aktive Registry-Pflicht allein aus Suchtreffern.')
    else:
        status, reason = assignments.get(family, ('detail_review_open',
            'Konkrete Fundstelle bekannt, aber Definition, dynamische Erzeugung und aktiver Ladeweg fuer diese Familie noch nicht gemeinsam belegt. Nächster Einstieg: ' + row['sample']))
    if family == 'chip-select':
        reason += ' Token chip-select-- ist Maskierungsfragment, keine fertige Klasse; dynamische Statuswerte gesondert behandeln.'
    output.append([family, status, row['sample'], reason])
assert len(output) == 117 and len({r[0] for r in output}) == 117
assert set(assignments) <= {r['family'] for r in rows}
with (OUT / 'UI_REGISTRY_REVERSE_TRIAGE.csv').open('w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['family', 'classification', 'template_evidence', 'reason_and_remaining'])
    w.writerows(output)
print(dict(Counter(r[1] for r in output)))
