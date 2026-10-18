# Verbindlicher Umsetzungsplan für Agenten

Stand: 18.10.2026. **U1 ist in Arbeit und insgesamt nicht abgeschlossen.**
Dieser Plan konsolidiert vorhandene Entscheidungen und Nachweise; er ist kein neuer Audit.
Die aktuelle Beauftragung umfasst die fortlaufende lokale Umsetzung bereiter Pakete
mit Tests, Dokumentation und lokalen Commits. Keine Produktionsfreigabe.

## Zuständigkeit der Dokumente

| Dokument | Verbindliche Aufgabe |
|---|---|
| [AGENT_HANDOFF.md](AGENT_HANDOFF.md) | Kurzer Einstieg, Ausgangsstand, Arbeitsgrenzen |
| Dieses Dokument | Einzige aktuelle Paketfolge, Restarbeit, Abhängigkeiten und Abschlusskriterien |
| [README.md](README.md) | Initiative und Nachweisregister abgeschlossener lokaler Pakete U1a–U1y |
| [Gesamtvorlage](RESTABDECKUNG_GESAMTVORLAGE.md) und dortiges Entwurfsverzeichnis | Bestätigte Fachregeln und Gestaltung; keine konkurrierende Ausführungswarteschlange |
| Einzelne U1-Paketdokumente | Technischer Vertrag, tatsächlich ausgeführte Tests, Grenzen des jeweiligen Pakets |
| [FINDINGS.md](FINDINGS.md), [PAKETREGISTER.csv](PAKETREGISTER.csv) | Historische 141 Befunde und primäre U1–U6-Zuordnung; keine aktuellen Erledigt-Markierungen |
| [COMPLETION_PLAN.md](COMPLETION_PLAN.md) | Historischer Auditplan K0–K6, nicht der Umsetzungsplan U1–U6 |

Aktuelle Nutzeraufträge gehen vor. Bestätigte Fachregeln bleiben massgeblich;
dieser Plan ändert keine davon. Bei Widerspruch zwischen Regel und Code den
konkreten Unterschied im betroffenen Paket festhalten. Nur eine tatsächlich
fehlende Fachentscheidung gezielt erfragen; F1/F2/R13 nicht erneut insgesamt abstimmen.
Alte Übergaben und datierte «Nächstes»-Absätze sind Verlauf, keine Arbeitsaufträge.

## Gesicherter Stand und Statusbegriffe

App-Basis: `3b85caa` auf `codex/u1y-onboarding-delivery`, separate jüngste
Migration `9405a7a`. Davor U1x `95c213a` / Migration `2c288ba`, U1w `536242d`,
U1v `74077f0` / Migration `24e68fc`. Die Dokumentationskonsolidierung baut auf
dieser Kette auf. Tatsächlichen Branch, HEAD, Vorfahren und lokale Änderungen
bei jedem Einstieg prüfen; niemals wegen eines älteren Übergabetextes zurücksetzen.

Zwei getrennte Zustände verwenden:

- **Lokale Umsetzung:** geplant → bereit → in Arbeit → lokal geprüft.
- **Externe Abnahme:** nicht erforderlich / offen / belegt. «Offen» ist kein
  Nachweis eines Fehlers, «lokal geprüft» kein Nachweis von Produktionsreife.

U1a–U1y sind lokale Pakete mit den im README und ihren Einzelunterlagen genannten
Prüfergebnissen. Diese Ergebnisse werden hier nicht zu einem neuen Gesamttest
zusammengezählt. U1 enthält weiterhin offene Befunde, Fachverträge und Abnahmen.
U2–U6 sind geplant; aus dieser Konsolidierung folgt keine neue Umsetzung dieser Pakete.

## Gesamtfolge U1–U6

| Bereich | Noch zu lieferndes Ergebnis | Abhängigkeit / Abschlussnachweis |
|---|---|---|
| U1 Zugang und Datenschutz | Restliste unten: Cache, Sichtbarkeit, Rollen-/Feldrechte, Recovery und Abnahmen | Alle betroffenen Einstiege serverseitig abgesichert; lokale Negativtests und relevante externe Nachweise |
| U2 Datenintegrität und Geldflüsse | B01, F3–F7, G1–G3, K1 in kleinen Transaktionspaketen umsetzen: Zahlungszuordnung, Forderungen, Erstattung, Zuschuss, Teilstorno, Jahreswechsel | Benötigte U1-Rechteverträge; Summenerhalt, atomare Fehlerfälle, Wiederholung und Parallelität einschliesslich PostgreSQL |
| U3 Fachabläufe und Wiederaufnahme | Event, Beiträge, Merch, Dokumente/Drive und Revision je als zusammenhängender Ablauf; B02 nur persönliche Anzeige | Jeweils nötige U1-/U2-Grundlage; Erfolg, Zurück, Abbruch, Fehler, Wiederholung und parallele Änderung geprüft |
| U4 Gemeinsame Oberfläche | Bestätigte Entwürfe pro Ablauf in gemeinsame Komponenten und vollständige Seiten überführen | Mit U3 pro Ablauf; Mobil/Tablet/Desktop, hell/dunkel, Fokus, Scrollen und Eingabeerhalt abnehmen; ausstehende Inhaltsrechte separat |
| U5 Performance und Betrieb | Messbare Verbesserungen, PWA-Updates, Mail-/Drive-Fehlerbehandlung und Betriebsevidenz | Begleitend; Vorher/Nachher-Messung und [Betriebsnachweise](OPERATIONS_EVIDENCE_REGISTER.md), keine unautorisierten Live-Prüfungen |
| U6 Altlasten und Pflege | Überholte Wege, Assets und Dokumente nach Ersatz entfernen; Merch-Daten erhalten | Erst nach jeweiligem Ersatz in U3/U4; Aufrufer, Weiterleitungen und alte Clients prüfen, Datenmigration separat; Game nicht Bestandteil |

U1 und U2 liefern Grundlagen. Eine noch ausstehende Geräteabnahme blockiert nicht
automatisch unabhängige lokale Arbeit; die konkrete Abhängigkeit entscheidet.
U3/U4 pro Fachablauf schneiden, keinen gesamten Rollen- oder UI-Umbau auf einmal starten.
Vor Umsetzung eines späteren Bereichs dessen bestätigten Entwurf aus dem
[Entwurfsverzeichnis](RESTABDECKUNG_GESAMTVORLAGE.md) lesen und ein begrenztes Paket ableiten.

## U1-Restfolge

Genau ein Paket ist **bereit / nächstes Paket**. Weitere Zeilen sind geplante
Restarbeit; ihre Feinabgrenzung erfolgt anhand der genannten Quellen vor Codeänderungen.

| Reihenfolge / ID | Lokal | Umfang und Abschlusskriterium |
|---|---|---|
| 1 / **U1z** | lokal geprüft | Cache-Nutzertrennung A-010; vollständiger Arbeitsvertrag im nächsten Abschnitt |
| 2 / U1-R02 | lokal geprüft | A-026/A-037/A-042: Sichtbarkeit von Events, internen Bewertungen und Aggregaten konsistent machen. Eingabewechsel all/board, Board-Meeting-Regel, Listen/Detail/API/Kalender/Dashboard prüfen. Öffentliche Aggregate erlauben, interne Namen/Kommentare und geschützte Eventdetails nicht offenlegen. Bestehende Forderungen nicht durch unsichtbare Events verlieren. Quellen: FINDINGS, Rollenentscheidungen, Bewertungs- und Public-Entwurf. Lesergruppe am 18.10.2026 bestaetigt: alle Mitglieder mit Eventzugriff; [Nachweis](U1_R02_SICHTBARKEIT.md). |
| 3 / U1-R03 | lokal geprüft | A-071: Beleg-/Dokumentauswahl und manipulierte Schreibanfragen nach denselben Rechten filtern. Keine fremden Beträge, Beschreibungen oder Board-Eventnamen über Optionslisten. R13-Belegrechte berücksichtigen; keine neuen Rollen einführen. |
| 4 / U1-R04 | Matrix lokal geprüft; Durchsetzung offen | F2/R13 zunächst als explizite Aktion-/Rolle-/Feldmatrix mit Ist-Zuordnung und Negativfällen konkretisieren. Danach getrennte Folgepakete für Delegationen, sensible Felder und Dokumentrechte nummerieren; je Paket serverseitige Durchsetzung und Tests. Vorstand ist nicht Admin; Bereichsrechte, Organisator, Revision und Admin-Stellvertretung gemäss bestätigten Regeln. Revisionszustände mit U2/U3 koordinieren. Kein Gesamtumbau in einem Paket. |
| 4a / U1-R04a | lokal geprüft | Sechs Pass-/ID-Felder lesend fuer Reisekommissar mit Step-Up; Feld-/Rollen-/Fehlerregression. Vertrag: [Rechtematrix](U1_R04_RECHTEMATRIX.md). |
| 4b1 / U1-R04b1 | lokal geprüft | Grundlage und erste travel_documents-Freigabe; [Nachweis](U1_R04B1_BEREICHSFREIGABEN.md), Migration ee39355 separat. |
| 4b2 / U1-R04b2 | lokal geprüft | Finanz-Lese-/Bearbeitungsfreigaben mit Negativtests; Revisionseigenbestaetigung und Zustandsumbau bleiben R04d. |
| 4b3 / U1-R04b3 | lokal geprüft | Reisebereich fuer Reisekommissar/gezielte Freigabe; keine Ausweitung auf fremde andere Events. |
| 4b4 / U1-R04b4 | lokal geprüft | Merchbereich fuer Marketing/gezielte Freigabe an bestehenden Mutationswegen; Zielsystemwechsel bleibt U3. |
| 4c / U1-R04c | c1–c3 lokal geprüft, externe Abnahme offen | Dokumentklassifikation, Auswahl/Listen/Download/Mutationen; Altbestand am 18.10. bestaetigt: bis Klassifikation nur Systemadmin; direkte Drive-Abnahme separat. |
| 4c1 / U1-R04c1 | lokal geprüft | Datei-/Ordnerpolicy und Historie, gemeinsame Servicepruefung; Migration separat. Vertrag U1_R04C_DOKUMENTRECHTE.md. |
| 4c2 / U1-R04c2 | lokal geprüft | Adminzuordnung und durchgaengige Route-/Service-/UI-Grenzen einschliesslich Altbestand und Archiv. |
| 4c3 / U1-R04c3 | lokal geprüft | Referenz-/Aufbewahrungspruefung vor endgueltigem Loeschen; Abschlussregression, direkte Drive-Abnahme bleibt extern. |
| 4d / U1-R04d | geplant; mit U2/U3 | Revisions-Pruefstand und begruendete Ruecknahme, Admin-Stellvertretung; keine reine Rollenlockerung. |
| 5 / U1-R05 | aufgeteilt in a–c | F1-Restvertrag für Linkzwecke, Adresse/Aktion, Ablauf, Ersatz, Einmalverbrauch und Kontolebenszyklus gegen U1o/q/r/v/y abgleichen. Nur nicht abgedeckte Wege umsetzen, Altlinks ausdrücklich behandeln. A-084-Mailnormalisierung als verbleibende Randbedingung prüfen, keine neue Kontozusammenlegung erfinden. U1w/x/y-Bestätigungen und versionierte Login-Identitäten erhalten. |
| 5a / U1-R05a | lokal geprüft | Hauptadressbindung der Reset-/Aktivierungslinks, Altlinks und Adresswechsel; Vertrag U1_R05_LINKRESTVERTRAG.md. |
| 5b / U1-R05b | **bereit / nächstes Paket** | Einheitliche Hauptmailnormalisierung, Lookup und DB-Eindeutigkeit ohne Kontozusammenlegung. |
| 5c / U1-R05c | geplant | Persistierte Resetlink-Ausgabe vor gebundenem Versand, kontrollierter Zustellstatus. |
| 6 / U1-R06 | geplant | A-121: irreführenden Backup-Code-QR-Export beseitigen oder durch nachweislich dekodierbare lokale Ausgabe ersetzen. Vor Code den gewählten minimalen Weg dokumentieren; kein externer QR-Dienst, keine Code-Leaks in Logs/Cache. U1u-Einmalanzeige erhalten. |
| 7 / U1-R07 | geplant | F1-Admin-Notfallweg: lokaler Ablauf und synthetischer Wiederherstellungsnachweis für den einzigen Admin, Backup-Codes und technische Wiederherstellung über eigenes Hosting. Kein zusätzlicher Admin, kein Schlüsselwechsel. Tatsächliche Hosting-Abnahme separat autorisieren. |
| 8 / U1-R08 | geplant | U1-Abschlussabgleich: verbleibende Rechte-/Recovery-/Widerrufsfälle und externe Nachweise zusammenführen. Offene Punkte nicht durch einen grünen SQLite-Lauf schliessen. |

### U1z: Cache-Nutzertrennung

**Problem und Quellen:** A-010 beschreibt einen nicht nutzergebundenen dynamischen
Service-Worker-Cache. Historisch wurde auch `private/no-store` gespeichert;
ein realer kontoübergreifender Browserabfluss ist damit noch nicht nachgewiesen.
Vor Umsetzung den aktuellen Service Worker, Cache-Header, Logout/Kontowechsel,
Updatepfad und Testmöglichkeiten gezielt lesen. Pflichtquellen: AGENTS,
ARCHITECTURE, CONVENTIONS, UI, UI-Regel und A-010. Kein neuer Gesamtaudit.

**Technischer Vertrag vor Code:** Explizite Cache-Zulassung für öffentliche/statische
Ressourcen definieren. Personenbezogene Antworten, private APIs, Dokumentdownloads
und tokengebundene Inhalte dürfen weder neu gespeichert noch aus bisherigen
dynamischen Caches als Offline-Ersatz geliefert werden. `private` und `no-store`
beachten. Bekannte alte App-Caches beim Update kontrolliert bereinigen; fremde
Origin-Caches nicht pauschal löschen. Kein neues Offline-Fachfeature.

**Regression und Abnahme:**

1. Synthetisch Konto A anmelden, private Antwort abrufen, abmelden und Konto B
   anmelden; mit und ohne Netz niemals Antwort von A erhalten. Ebenso Abmeldung
   ohne Folgeanmeldung prüfen.
2. Bereits gefüllten alten Cache sowie neue Antworten mit `private/no-store`
   abdecken. Private API, Download und tokengebundener Kalenderweg gesondert
   erfassen; keine Tokens in Prüfausgaben.
3. Öffentliche/statische Offline-Ressourcen bleiben nutzbar; Update von bestehendem
   Worker und fehlgeschlagene Requests haben definierte, verständliche Ergebnisse.
4. Isolierte Regression ohne dotenv oder ausgehende Verbindungen. Falls ein
   JS-Harness nötig ist, ebenfalls mit synthetischen Requests/Responses und
   gesperrtem Netz; vorhandenen Python-Runner für betroffene Backend-Tests verwenden.
5. Dokumentieren, was Simulation und was echter Browsernachweis ist. Installierte
   PWA, mehrere Tabs, Browser-Cache und reale Geräte bleiben ohne Ausführung offen.

**Lieferung:** Begrenzte Änderung, passende Regression, `U1Z_CACHE_NUTZERTRENNUNG.md`
mit Vertrag/Ergebnissen/Grenzen, nötige Anchor-/Cache-Buster-Pflege, README-Zeile
und Aktualisierung dieser Restfolge. Keine Rollenänderung, keine Migration erwartet.

## Rückverfolgung der U1-Befunde

Alle 26 primär U1 zugeordneten Befunde aus dem historischen Paketregister:
«Lokal» bezeichnet nur den dokumentierten Umfang, nicht externe Abnahme.

| Befund | Lokaler Nachweis oder verbleibender Auftrag |
|---|---|
| A-010 | Lokal: [U1z](U1Z_CACHE_NUTZERTRENNUNG.md); Browser/Geraete offen |
| A-026 | Lokal: [U1-R02](U1_R02_SICHTBARKEIT.md); Browser/Kalenderclients offen |
| A-035 | Lokal: [U1g](U1G_LOGIN_RUECKKEHR.md), [U1h](U1H_STEP_UP_RUECKKEHR.md), [U1i](U1I_BEWERTUNG_RUECKKEHR.md), [U1j](U1J_MERCH_DOKUMENT_RUECKKEHR.md) |
| A-037 | Lokal: [U1-R02](U1_R02_SICHTBARKEIT.md); Browser/Kalenderclients offen |
| A-042 | Lokal: [U1-R02](U1_R02_SICHTBARKEIT.md); Browser/Kalenderclients offen |
| A-043 | Lokal: [U1e](U1E_REMINDER_RECHTE.md) |
| A-071 | Lokal: [U1-R03](U1_R03_BELEGAUSWAHL.md); umfassende R13-Matrix folgt |
| A-075 | Lokal: [U1c](U1C_STEP_UP.md); aktionsgebundener Folgevertrag U1w |
| A-076 | Lokal: [U1t](U1T_PFLICHTWECHSEL.md) |
| A-077 | Lokal: [U1v](U1V_SITZUNGS_GERAETEWIDERRUF.md); PostgreSQL/Geräte offen |
| A-078 | Lokal: [U1g](U1G_LOGIN_RUECKKEHR.md) |
| A-079 | Lokal: [U1f](U1F_BACKUP_CODES.md); echter Parallelitätsnachweis offen |
| A-080 | Lokal: [U1u](U1U_MFA_BACKUP_NEUEINRICHTUNG.md) |
| A-081 | Lokal: [U1b](U1B_LOGGING.md) |
| A-082 | Lokal: [U1v](U1V_SITZUNGS_GERAETEWIDERRUF.md); Geräte offen |
| A-083 | Lokal: [U1k](U1K_MFA_RESET_BESTAETIGUNG.md); visuelle Abnahme offen |
| A-086 | Lokal: [U1a](U1A_DATENERHALT.md) |
| A-087 | Lokale Form-Bereitstellung bereits in [U1a](U1A_DATENERHALT.md) dokumentiert; R13-Feldrechte bleiben U1-R04 |
| A-088 | Lokal: [U1o](U1O_GOOGLE_VERIFIKATION.md) |
| A-089 | Lokal: [U1s](U1S_DRIVE_WIDERRUF.md); externe Rechte und Mehrfachzuordnung offen |
| A-090 | Lokal: [U1p](U1P_LETZTER_ADMIN.md); PostgreSQL-Parallelität offen |
| A-110 | Lokal: [U1b](U1B_LOGGING.md) |
| A-113 | Lokal: [U1d](U1D_CRON_TEST.md) |
| A-121 | Offen → U1-R06 |
| A-140 | Lokal: [U1v](U1V_SITZUNGS_GERAETEWIDERRUF.md), `test_activation_with_existing_mfa_does_not_log_in` in [Regression](../../../tests/routes/test_auth_revocation.py); Altlinkvertrag zusätzlich U1-R05 |
| A-141 | Lokal für dokumentierte Wege: [U1q](U1Q_PASSWORTLINK_WIDERRUF.md), [U1r](U1R_MFA_LINK_WIDERRUF.md), U1v/y; vollständiger Zweck-/Altlinkabgleich U1-R05 |

Zusätzlich umgesetzt: A-084 anteilig in U1l/m, A-085 in U1n, A-139 in U1y,
F1-Aktionsbestätigung in U1w/x/y. Ihre historischen Primärpakete im CSV werden
nicht rückwirkend umgeschrieben. A-137 (allgemeine Audit-/Commit-Fehler) ist durch
U1y nicht global erledigt und bleibt bei U2/U5. Für alle 141 Befunde gilt weiterhin
die Primärzuordnung im CSV; beim jeweiligen Paketstart gegen aktuelle Umsetzung
abgleichen und den Nachweis ergänzen, nicht einen neuen Gesamtaudit eröffnen.

## Ausstehende Entscheidungen und externe Nachweise

| Punkt | Was konkret fehlt | Arbeitsgrenze |
|---|---|---|
| D-01: Google-Adresse an mehreren Mitgliedern | Entscheiden, ob und wie diese Zuordnung erlaubt ist; Widerruf eines Kontos kann andere betreffen. U1s dokumentiert die Grenze. | Keine stillschweigende 1:1-Regel; vor betroffenem Rollout gezielt klären, U1z unabhängig |
| PostgreSQL | Synthetische Migrationen Upgrade/Downgrade/Upgrade sowie konkurrierende Widerrufe, Einmalverbrauch, letzter Admin und Onboarding unter echten DB-Sperren | Separate isolierte Testumgebung und passender Auftrag; keine Produktionsdaten. SQLite ersetzt diesen Nachweis nicht. |
| Browser / Geräte | Session, Remember-me, MFA-Zwischenschritt, vertrauenswürdiges Gerät, mehrere Tabs und installierte PWA nach Widerruf/Update | Versionierte Login-Identitäten aus U1v verwenden; konkrete Geräte und Fälle protokollieren |
| Mail | Reale Zustellung, Linkadresse, Wiederholung, Fehlerstatus und Recovery | Fake-Mailservice beweist keine Zustellung; kein Versand an echte Mitglieder ohne Auftrag |
| Drive | Reale Mitgliedschaften, Gruppen-/Domainrechte, individuell freigegebene Dateien, alte Adressen und Wiederholung nach Fehler | U1s deckt nicht alle externen Rechte ab; keine unautorisierten Inventare oder Freigabeänderungen |
| Admin-Notfall | Ausführbare Wiederherstellung auf eigener Hosting-Infrastruktur | Erst lokaler Vertrag; Live-Nachweis separat, CRYPTO_KEY bleibt unverändert |
| Weitere Betriebs-/Inhaltsabnahmen | Offene Einträge im [Betriebsregister](OPERATIONS_EVIDENCE_REGISTER.md), Nutzungsrechte für öffentliche Inhalte | Je passendem U4/U5-Paket behandeln; keine pauschale Produktionsfreigabe |

## Arbeitsablauf und Fertigkriterien für Agenten

Bei «weiter» im bestehenden lokalen Auftrag das nächste bereite Paket verwenden,
sofern der aktuelle Nutzerauftrag keine andere Grenze setzt. Branch/HEAD/Änderungen
prüfen, relevante Anchor-Docs und Paketquellen lesen, technischen Vertrag vor
Code festhalten und das begrenzte Paket vollständig liefern. Abbruch, Fehler,
Einmalverbrauch und Parallelität dort konkretisieren, wo sie betroffen sind.

Für Python-Regression den dokumentierten [isolierten Runner](run_existing_tests.py)
verwenden: synthetische Daten, kein dotenv, keine ausgehenden Verbindungen.
Keine realen Konten, Schlüssel oder Services für lokale Tests verwenden. Tatsächlich
ausgeführte Befehle, Ergebnisse, korrigierte Fehler und verbleibende Grenzen im
Paketnachweis dokumentieren; keine vermuteten oder historischen Ergebnisse als neue ausgeben.

Zum Paketabschluss Code und passende Regression fertigstellen, relevante Anchor-Docs
pflegen, README-Nachweiszeile ergänzen und hier Status/Restfolge nachführen.
Handoff kurz halten, keine neuen Chronologien voranstellen. Erst nach Abschluss
genau einen nächsten Auftrag auf «bereit» setzen. Eine fehlende Detailentscheidung
isolieren und unabhängige Arbeit fortsetzen; keine erneute pauschale Fachabstimmung.

Lokal auf der bestehenden Branchkette sichern, fremde Änderungen erhalten und nur
eigene Dateien committen. Migrationen immer separat. Kein Push, Merge auf master,
Deploy, Produktionsdatenzugriff oder Schlüsselwechsel. Keine neuen Chats oder
Agenten automatisch starten.

**U1 insgesamt fertig** ist erst zulässig, wenn die Restfolge einschliesslich
F1/F2/R13 umgesetzt oder ausdrücklich fachlich ausgenommen ist, jeder U1-Befund
einen konkreten Nachweis besitzt und alle relevanten externen Abnahmen belegt
sind. Lokale Fertigstellung und Freigabe zur Veröffentlichung sind getrennte Entscheidungen.

## Nachweis der Dokumentationskonsolidierung

16.10.2026: Ausschliesslich Dokumentation geändert. Lokal geprüft: 141 Einträge
im unveränderten Paketregister; alle 26 U1-Befunde genau einmal in der obigen
Nachweistabelle; 25 U1a–U1y-Zeilen im README; genau ein nächstes bereites Paket;
alle lokalen Dateilinks in neuem Plan und neuem Handoff vorhanden. Der Git-Blob
des bewahrten Übergabeverlaufs stimmt mit dem ursprünglichen Handoff überein.
`git diff --check` ohne Fehler. Keine neuen App-Regressionstests ausgeführt,
keine PostgreSQL-, Geräte-, Mail- oder Drive-Abnahme vorgenommen.
