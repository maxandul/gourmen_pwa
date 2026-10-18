# U1-R04 – Verbindliche Aktion-/Rolle-/Feldmatrix

Stand 18.10.2026, lokale Quelleneinordnung nach U1-R03 (`0601d81`).
Quellen: ROLLEN_ENTSCHEIDUNGEN.md (F2/R13), CONVENTIONS.md, DOMAIN.md,
RESTABDECKUNG_GESAMTVORLAGE.md. Keine neuen fachlichen Rollen.
Diese Matrix ist ein Implementierungsvertrag, kein Nachweis fertiger Durchsetzung.

## Aktionen und bestehende Durchsetzung

| Aktion / Daten | Zielberechtigung | Ist-Einstieg / Luecke | Folgepaket / Negativfall |
|---|---|---|---|
| Eigenes Profil lesen/aendern | eigenes aktives Mitglied | member.profile, bestehend | fremde ID darf keine eigene Bindung ersetzen |
| Eigene sensible Angaben | eigenes Mitglied + frischer Step-Up | member.profile, U1a/c; bestehend | ohne/abgelaufener/fremder Step-Up kein Inhalt |
| Alle sensiblen Angaben lesen/aendern | Systemadmin + Step-Up | admin.member_sensitive, bestehend | Vorstand/Funktion/Organisator allein kein Zugriff |
| Reisedokumentangaben anderer lesen | Reisekommissar + Step-Up; spaeter gezielte Bereichsfreigabe | aktuell nur Adminformular vorhanden | R04a: nur Pass-/ID-Nummer und Ausstellungs-/Ablaufdatum, keine Allergien/Fremdfelder; POST verboten |
| Zahlungsangaben anderer | Schatzmeister + Step-Up, nur vorhandene Felder | MemberSensitive hat kein definiertes Zahlungsfeld; keine neue Pflicht einfuehren | R04a: leere Feldmenge, kein Zugriff auf den Gesamtpayload |
| Bereichsfreigabe vergeben/entziehen | nur Systemadmin, frischer aktionsgebundener Beweis | kein Freigabemodell | R04b: serverseitige Bereichspruefung, Widerruf, kein Selbstaufstieg/kein geerbtes Adminrecht |
| Event lesen / Ratings lesen | bestehende Event-Audience; interne Ratings alle Eventleser | U1-R02 vereinheitlicht | Board-Negativmatrix vorhanden |
| Event bearbeiten / Teilnahme / BillBro | zugewiesener Organisator, Systemadmin; Reisen zusaetzlich Reisekommissar | events.edit/BillBro Organisator/Admin; Reisebereich nicht durchgaengig | R04b: Reiseberechtigung gilt nicht fuer fremde Monatsessen oder Rollenverwaltung |
| Event anlegen | Systemadmin; Reiseanlage Reisekommissar; delegierte Bereiche | admin.create_event nur Admin | R04b: manipuliertes Eventtyp-Feld darf Reisebefugnis nicht ausweiten |
| Merch / oeffentliche Inhalte pflegen | Marketingchef, Systemadmin, passende Bereichsfreigabe | Merch-Mutationen in admin.py nur Admin; Public-Inhalte teils statisch | R04b/U3: vorhandene Mutationswege abgleichen, keinen neuen CMS-Service erfinden |
| Buchhaltung schreiben | Schatzmeister/Systemadmin, passende Bereichsfreigabe | accounting _is_treasurer/_require_funktion | R04b: Finanzfreigabe gewaehrt keine Admin-/sensible Vollrechte |
| Buchhaltung lesen / pruefen / beanstanden | Revisor, Schatzmeister, Systemadmin; passende Lesefreigabe | accounting _require_funktion | R04b/R04d: Read-only darf nicht buchen/importieren |
| Revision bestaetigen | Revisor; Systemadmin als markierte Stellvertretung | accounting / AccountingService; Zustandsvertrag gesondert | R04d mit U2/U3: Schatzmeister keine eigene Bestaetigung, Admin-Ausnahme sichtbar |
| Revision zur Bearbeitung zuruecknehmen / Jahr oeffnen | Schatzmeister/Systemadmin jeweils allein mit Grund | bestehende Zustandswege gegen F6/R13 abgleichen | R04d mit U2/U3: kein stilles Aendern gepruefter Fassung, Verlauf/Pruefstand erhalten |
| Beleg einreichen / eigener Status | aktives Mitglied | U1-R03, member.receipts | keine fremden Buchungsoptionen; kein Verlust eigener Forderung |
| Beleg lesen / zuordnen | Finanz-/Revisionsrollen/Admin; Einreichender eigener Vorgang; Eventrecht zusaetzlich | U1-R03 Auswahl/Download/Zuordnung; umfassende Finanzlisten noch offen | R04c: Listen/Export/Detail/API dieselben Grenzen |
| Gemeinsame Vereinsdokumente lesen | aktive Mitglieder | docs login_required, keine Klassifikation | R04c: Board-/Finanzdokument nicht im allgemeinen Suchergebnis |
| Vorstandsdokumente lesen | Vorstand/Systemadmin; Eventrecht zusaetzlich | Document hat nur Drive-ID/Parent/Uploader/Event, kein Bereich | R04c: direkte URL, Suchtreffer, Ordnerpicker und Archiv pruefen |
| Dokumente hochladen/pflegen/archivieren/wiederherstellen | zustaendige Bereichsrolle oder gezielte Pflegefreigabe; Systemadmin | docs Mutationen ueberwiegend nur login_required | R04c: gewoehnliches Leserecht erteilt kein Umbenennen/Verschieben; Zielordner pruefen |
| Dokument endgueltig loeschen | Systemadmin, Verknuepfungs-/Aufbewahrungspruefung | docs.hard_delete Admin; Schutzvertrag noch unvollstaendig | R04c: gebuchter Beleg/Referenzen sperren, Archiv erweitert keine Rechte |
| Direkter Drivezugriff | gleiche fachliche Grenzen wie App | externer Bestand nicht inventarisiert; keine lokale Freigabeaenderung | R04c externe Abnahme; keine Produktionsfreigaben entziehen |

## Explizite Feldmatrix

| Feldgruppe | Eigenes Mitglied | Systemadmin | Reisekommissar | Schatzmeister | Vorstand/Organisator/Marketing/Revisor allein |
|---|---|---|---|---|---|
| pass_nummer, pass_ausgestellt, pass_ablauf | Lesen/Schreiben + Step-Up | Lesen/Schreiben + Step-Up | Lesen + Step-Up | nein | nein |
| id_nummer, id_ausgestellt, id_ablauf | Lesen/Schreiben + Step-Up | Lesen/Schreiben + Step-Up | Lesen + Step-Up | nein | nein |
| allergien | bestehender eigener Weg + Step-Up | bestehender Adminweg + Step-Up | nein | nein | nein |
| fuehrerschein / unbekannte JSON-Schluessel | bestehende eigene/Admin-Wege beibehalten | bestehender Adminweg | nicht Teil der Pass-/ID-Ansicht | nein | nein |
| Zahlungsfelder | keine neuen Felder | keine neuen Felder | nein | aktuell keine definierte Feldmenge | nein |
| MFA-Geheimnis, Backup-Codes, Zugangstoken | nur bestehende zweckgebundene Sicherheitsablaeufe | kein pauschales Leserecht aus Bereichsfreigaben | nein | nein | nein |

Minimale Auslegung von R13 fuer R04a: neue Funktionsansicht ist **lesend** und
liefert nur die sechs eindeutig vorhandenen Pass-/ID-Felder. Keine pauschale
Herausgabe unbekannter verschluesselter Inhalte. Berechtigungen vor Entschluesselung
pruefen, Ausgabefelder vor Templateuebergabe selektieren, Cache no-store.

## Kleine Folgepakete und Reihenfolge

1. **U1-R04a – sensible Feldansicht**: sechs Pass-/ID-Felder lesend fuer Reisekommissar
   mit bestehendem Step-Up; eigene/Admin-Wege unveraendert. Rollen-/Feld-/POST-/
   Step-Up-Negativtests und synthetischer Fehler beim Entschluesseln.
2. **U1-R04b – Bereichsfreigaben**: explizite Scopes und aktive Freigaben,
   Verwaltung nur Systemadmin mit U1w/x-Bestaetigung; Migration separat.
   Bereichsweise Durchsetzung in separaten Teilpaketen (Finanzen, Reisen, Merch),
   keine neue Freigabe erteilt Systemadmin oder Revisionseigenbestaetigung.
3. **U1-R04c – Dokumentrechte**: Klassifikations-/Ordnervertrag und sichere
   Behandlung noch nicht klassifizierter Altdateien vor Implementierung festhalten.
   App-Pruefungen lokal, direkte Drive-Abnahme separat ohne Live-Zugriff.
4. **U1-R04d – Revisionsgrenzen**: versionsgebundener Pruefstand und begruendete
   Ruecknahme mit U2/U3 gemeinsam; keine isolierte Rollenlockerung vor Zustandsmodell.

R04b ist vor Umsetzung weiter in die genannten Bereiche zu schneiden.
R04c benoetigt eine konkrete Altbestands-/Klassifikationsregel, nicht allein einen
Foldernamenvergleich. Diese Entscheidung blockiert nicht R04a oder andere
unabhaengige lokale Pakete. U1 insgesamt bleibt offen.

## Lokale Pruefung dieses Matrixpakets

Nur Dokumentation. Quelleneinstiege in admin.py, member.py, events.py, accounting.py,
docs.py, MemberSensitive und Document gezielt abgeglichen. Keine neue App-Regression
fuer diesen Dokumentationscommit ausgefuehrt; letzte Pakettests bleiben getrennt.
Lokale Links und `git diff --check` beim Abschluss pruefen. Kein externer Nachweis.

18.10.2026 Nutzerentscheidung zu R04c: Noch nicht zugeordnete Dateien in der App
bis zur Klassifikation nur Systemadmin. Keine Aenderung direkter Drive-Freigaben.
