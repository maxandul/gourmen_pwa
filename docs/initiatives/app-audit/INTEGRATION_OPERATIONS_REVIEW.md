# Wiederverbindung, Integrationen und Betrieb – erster Durchlauf

Stand 2026-09-20. App unveraendert. Keine echten Dienste, Mails, Schluessel,
Produktionskonfigurationen oder Betriebslogs verwendet.

## Nachweise und Grenzen

- `check_offline_return.cjs`: fuenf Proben des originalen Inline-Scripts der
  vom SW referenzierten `static/offline.4ebb2a42.html`, synthetische DOM/Timer.
  [Ergebnisse](OFFLINE_RETURN_CHECKS.json). Kein echter Browser-Netzwechsel.
- `check_integration_contracts.py`: sechs Aufrufe originaler Places-/Mail-
  Methoden mit ersetzten Transporten/Loggern, gesperrtem Netzwerk und ohne DB.
  [Ergebnisse](INTEGRATION_CONTRACT_CHECKS.json). Keine gemessenen Wartezeiten.
- Diese elf Proben ergaenzen die zehn SW-Algorithmus-Proben und 120 Render-
  Messungen. Die 143 fachlichen Workflow-Szenarien bleiben separat gezaehlt.

## Wiederverbindung

OFF-01: Bei offline bleibt die Seite stehen. OFF-02/05: Online-Flag bzw.
Online-Event setzt den Status und einen vermeintlichen letzten Sync-Zeitpunkt,
anschliessend erfolgt nach 1.5 Sekunden Navigation auf `/`. Kein Fetch prueft
die App. OFF-03: Bereits geplanter Timer navigiert auch nach erneutem Offline-
Event. OFF-04: Drei modellierte Neuladungen desselben Fallback-Dokuments erzeugen
drei weitere Navigationen. Das belegt die Wiederholung unter dieser Annahme,
keine im Browser beobachtete Endlosschleife. A-107.

Empfehlung: Online-Flag als Hinweis verwenden, App-Erreichbarkeit separat
bewerten, Wiederholungen begrenzen und urspruengliches Ziel erhalten. Status
und Zeitstempel sollen tatsaechliche Verbindung/Abfrage widerspiegeln.
[MDN zum Online-Flag](https://developer.mozilla.org/en-US/docs/Web/API/Navigator/onLine).
Die Aussage zu gecachten Seiten im Fallback muss ausserdem mit dem aktuellen
SW-Vertrag abgeglichen werden: Navigationen werden dort nicht dynamisch gecacht.

## Dienste

| Dienst | Beobachtung | Einordnung |
|---|---|---|
| Places | Beide GET-Aufrufe ohne timeout; injizierter Timeout liefert leere Vorschlaege | A-108; Fehler und echte leere Treffer sind nicht unterscheidbar |
| Places-Logging | Autocomplete loggt params samt synthetischem API-Key auf INFO | A-110; reale Logs nicht untersucht |
| Mail/Resend | Explizite 15s im Test uebergeben; Timeout gibt success=false | Positiver Fehlervertrag, keine Zustellgarantie |
| Mail/SMTP fehlt | Ohne Host success=true mit Fehlertext, ohne Credentials success=true ohne Fehlertext | A-109; kein Transport aufgerufen |
| Admin-Mailtest | Prueft zusaetzlich message_id und warnt bei fehlender Konfiguration | Positiver Consumer; keine falsche Versandanzeige fuer diesen Zweig behaupten |
| Drive | Eigener Retry-Filter fuer ausgewaehlte HTTP-/Verbindungsfehler, maximal drei Versuche | Quellbefund; kein pauschales Fehlen von Retry behaupten |

Places sollte begrenzte Verbindungs-/Lesezeiten und einen unterscheidbaren
Fehlervertrag erhalten. Ein Requests-Timeout ist kein Gesamtlaufzeitbudget;
siehe [Requests-Dokumentation](https://requests.readthedocs.io/en/latest/user/quickstart/#timeouts).
Mail sollte angenommen, uebersprungen, fehlgeschlagen und versendet klar
unterscheiden. Hintergrundannahme bedeutet noch keine Zustellung.

## Betriebsgrenzen und naechste Pruefobjekte

- `railway.json` startet `start.sh` und prueft `/health`. Web-Zweig konfiguriert
  einen Gunicorn-Prozess mit acht Threads. Dies ist Repo-Konfiguration, keine
  Verifikation des laufenden Railway-Diensts oder seiner Kapazitaet.
- `/health` in `backend/app.py` gibt statischen App-Status aus; DB-Ping ist
  separat `/health/db`. `docs/CONVENTIONS.md` beschreibt fuer `/health` dagegen
  einen DB-Test. Im Dokumentationsabgleich aufloesen; keine Behauptung, dass
  ein Liveness-Endpunkt zwingend abhaengige Dienste pruefen muss.
- `MailService.send_async` startet einen Daemon-Thread und meldet queued.
  Persistenz, Wiederaufnahme nach Neustart und Zustellstatus sind nicht belegt.
  Shutdown-/Mehrfachversand-Szenarien und saemtliche Aufrufer noch pruefen.
- Drive-Client wird ohne projektspezifischen Transport-Timeout gebaut. Defaults
  der installierten Bibliotheken und gesamtes Retry-Budget noch untersuchen;
  daraus bisher keinen unbegrenzten Request ableiten.
- Cron-Zeitplan, Zeitzonen, parallele Laeufe, Ausfall/Wiederholung sowie Push-
  Transportgrenzen sind noch offen. Backup-Aufbewahrung, Restore-Probe und
  externe Monitoring-Konfiguration benoetigen eigene Nachweise.

Dieser Bericht schliesst den Betriebsdurchlauf nicht ab.

## Zweiter Durchlauf: Erinnerungen, Cron-Zugang und Hintergrundversand

Neun weitere isolierte Proben in `check_notification_boundaries.py`,
[Ergebnisse](NOTIFICATION_BOUNDARY_CHECKS.json). Originale Services, Routes und
Cron-Runner; Versand, Threadstart und einzelne Ergebnisgrenzen ersetzt.
Ein synthetisches Event, ein Mitglied/eine Subscription, SQLite im Speicher.
Token-Cleanup des Runners betrifft nur die leere lokale Testtabelle. Keine
echten Nachrichten, parallelen Prozesse, Produktion oder Transportlaufzeiten.
Diese neun technischen Grenzproben werden separat von den 143 bisherigen
fachlichen Workflow-Szenarien und 120 Render-Messungen gezaehlt.

| Probe | Beobachtung | Zuordnung |
|---|---|---|
| NOT-01 | Zwei unmittelbare 3-Wochen-Laeufe beauftragen Organisator und Mitglieder jeweils zweimal | A-111 |
| NOT-02 | Organisator false, Mitglieder success=false, trotzdem Batch success=true | A-112 |
| NOT-03 | Push 410 deaktiviert Subscription dauerhaft im Testbestand | Positiv |
| NOT-04 | Push 503 laesst Subscription aktiv | Positiv: temporaeren Fehler nicht als ungueltiges Geraet behandeln |
| NOT-05 | send_async gibt queued/success zurueck, bevor Worker ausgefuehrt wird; daemon=True | Annahme ist kein Zustellnachweis |
| NOT-06 | Spaeterer Workerfehler wird gewarnt, aendert fruehere Rueckgabe nicht | Keine persistente Warteschlange in dieser Methode |
| NOT-07 | Originale ProductionConfig ohne explizites ENV: normaler Cron ohne Token 401, /cron/test 200 mit Service-Aufruf | A-113 |
| NOT-08 | Explizites ENV=production sperrt /cron/test mit 403 | Sperre haengt vom zusaetzlichen Wert ab |
| NOT-09 | Originaler Gesamt-Runner liefert Exitcode 0 bei ersetztem Batch mit eingebetteten Versandfehlern | A-112 bis Prozessgrenze verfolgt |

### Schlussfolgerungen

- Die Reminder-Auswahl dokumentiert keinen dauerhaften Versandstatus pro
  Event/Erinnerungsart/Empfaenger. Bereits serielle Wiederholung erzeugt erneut
  Auftraege. Der Notification-tag ist kein serverseitiger Versandnachweis;
  tatsaechlich sichtbare Doppelmeldungen haengen auch vom Client ab. Parallele
  Aufrufe wurden nicht simuliert. Fuer eine spaetere Loesung atomare Reservierung,
  Versandresultate und gezieltes Wiederholen fehlgeschlagener Empfaenger planen.
- Batch-Erfolg bedeutet aktuell abgearbeitete Auswahl, nicht erfolgreichen
  Versand. Das wird vom Runner als Gesamterfolg behandelt. Uebersprungen,
  ohne Empfaenger, teilweise versendet und fehlgeschlagen sollten trennbar sein.
  Ein leerer Lauf muss dabei nicht als Fehler gelten.
- `/cron/test` benutzt weder die gemeinsame Cron-Authentifizierung noch eine
  explizit gesetzte Testfreigabe. ProductionConfig setzt DEBUG=False, aber kein
  ENV. Die isolierte Route mit dieser originalen Klasse zeigt daher den Bypass.
  Kein Beleg fuer externen Zugriff auf das aktuelle Railway-Deployment.
- Hintergrund-Mail ist ein Daemon-Thread im Webprozess. Prozessabbruch,
  Wiederaufnahme und Doppelversand bleiben offen; nicht als reproduzierten
  Nachrichtenverlust ausweisen. Anforderungen an dauerhaften Versand festlegen.

### Verbleibende Grenzen

Zeitfenster basieren auf datetime.utcnow(): 3-Wochen-Auswahl +/-12 Stunden,
Wochenreminder nur am UTC-Montag, Bewertungen am UTC-Vortag. Verspaetete Laeufe,
Sommerzeit, lokale Eventzeit und Nachholen verpasster Laeufe gezielt pruefen.
Der tatsaechliche Scheduler-Zeitplan ist noch nicht belegt. `/cron/status`
ist oeffentlich und sein last_check ist die aktuelle Abfragezeit, kein
gespeicherter letzter erfolgreicher Lauf; Sichtbarkeit/Bezeichnung bewerten.
Push-Transportbudget und Legacy-Notifier bleiben ebenfalls offen.

## Dritter Durchlauf: Zeitfenster und Push-Transportbudget

Fuenf Proben in `check_reminder_windows.py`,
[Ergebnisse](REMINDER_WINDOW_CHECKS.json). Originale Auswahlabfragen mit
kontrollierter UTC-Uhr; ein synthetisches Event und ersetzter Versand.
Die Zeitfenster-Proben vergleichen jeweils einen passenden Lauf mit dem
Folgetag. Keine echten Scheduler-Ausfaelle, keine Sommerzeit-Simulation.

| Probe | Passender Lauf | Folgetag |
|---|---|---|
| TIME-01: 3-Wochen, Event 12.10.2026 08:00 | 21.09. 08:00: ein Event | 22.09. 08:00: null |
| TIME-02: Wochenreminder, Event Freitag 25.09. | Montag 21.09.: ein Event | Dienstag 22.09.: null |
| TIME-03: Bewertung, Event 20.09. 19:00 | 21.09. 08:00: ein Event | 22.09. 08:00: null |

**A-114:** Ein Nachholfenster fuer verpasste Laeufe fehlt. Das ist ein belegter
Auswahlvertrag mit offener Produktentscheidung, kein Nachweis eines real
verpassten Versands. Ohne dauerhaftes Versandregister (A-111) wuerde simples
Vergroessern der Fenster zugleich mehr Wiederholungen zulassen. Gemeinsam
festlegen, wie lange welcher Reminder noch sinnvoll ist und wie bereits
bearbeitete Empfaenger erkannt werden.

**A-115:** TIME-04 prueft den originalen aktuellen Push-Aufruf: kein timeout.
TIME-05 prueft die lokal installierte Funktion pywebpush.webpush: ihr Default
None wird explizit an WebPusher.send weitergegeben. Dessen Code reicht diesen
Wert an requests_method.post weiter. Der dort sichtbare Ersatzwert 10000 greift
nicht, wenn timeout bereits explizit None ist. Kein echter Push, kein echter
VAPID-Key, keine gemessene Blockade. requirements.txt pinnt pywebpush==2.0.3;
der in Produktion installierte Stand wurde nicht verifiziert.

Empfehlung: begrenzte Verbindungs-/Lesezeiten pro Versandversuch und ein
Gesamtbudget fuer einen Lauf bestimmen; Zeitfehler pro Empfaenger ausweisen
und spaetere Empfaenger weiterverarbeiten. Kein blindes Retry erfolgreich
uebermittelter Pushs. Das ergaenzt den Ergebnisvertrag A-112.

Weiter offen: lokale Zeit-/Sommerzeitgrenzen, echter Scheduler-Zeitplan und
Betriebsnachweise. Legacy-Notifier ist nicht allein aufgrund seines Namens
verwaist: BillBro-Routes rufen send_billbro_start/send_billbro_reminder auf.
Seine Fehlerbehandlung und Subscription-Loeschung als naechsten begrenzten
Durchlauf pruefen; aktuelle positive 410/503-Proben gelten nur fuer PushNotificationService.

## Vierter Durchlauf: Legacy-Notifier und BillBro-Rueckmeldung

Sechs Proben in `check_legacy_notifier.py`,
[Ergebnisse](LEGACY_NOTIFIER_CHECKS.json). Originaler Service und einmal
originaler BillBro-POST als Organisator, SQLite im Speicher, Push/Mail ersetzt.
CSRF in der Testkonfiguration deaktiviert; keine erneute CSRF-Pruefung.
Keine echten Nachrichten oder Abonnements betroffen. Die sechs Proben werden
als technische Grenzproben separat gezaehlt; keine Aenderung der bisherigen
143 fachlichen Workflow-Szenarien oder 120 Render-Messungen.

| Probe | Ergebnis | Einordnung |
|---|---|---|
| LEG-01 | Injizierter Requests-Timeout: Subscription danach geloescht | A-116 |
| LEG-02 | Injizierte WebPushException mit HTTP 503: ebenfalls geloescht | A-116 |
| LEG-03 | is_active=False: Transport wird dennoch aufgerufen | A-116; Statusvertrag inkonsistent |
| LEG-04 | BillBro-Start ohne Subscription: HTTP 302 und Erfolgsmeldung ueber gesendeten Push; null Push-/Mail-Aufrufe | A-117 |
| LEG-05 | Registrierung zweiten Geraets entfernt erstes Geraet | A-118 |
| LEG-06 | Fehlerhafte Registrierung ohne keys rollt zurueck und erhaelt bisherigen Bestand | Positives Gegenbeispiel |

Ursache A-116: `_send_to_subscription` reduziert alle Fehler auf False;
der Aufrufer loescht bei jedem False die Zeile. Dazu fehlt is_active in der
Auswahl. Das unterscheidet sich vom aktuellen Dienst, der im geprueften
503-Fall das Geraet erhaelt. Beide Dienste nutzen dieselbe Subscription-Tabelle.

Ursache A-117: `_send_fallback_notification` loggt nur und liefert True.
`send_billbro_start` zaehlt dies als Erfolg, die Route formuliert daraus Versand
an alle Teilnehmer. Die Probe hat exakt einen Teilnehmer; gemischte Teilfehler
und die zaehlerbezogene Uebertreibung bei mehreren Empfaengern bleiben offen.
Keine Verpflichtung ableiten, zwingend Ersatz-Mails zu senden: Entscheidung
ueber den Kanal treffen, Rueckmeldung aber an wirkliche Ergebnisse binden.

Ursache A-118: `subscribe_user_to_push` loescht alle Zeilen des Mitglieds vor
Eintrag des neuen Endpoints. `/notifications/subscribe` ist registriert und
ruft diese Methode auf; keine Nutzung durch einen aktuellen Browser bewiesen.
Bei Konsolidierung Mehrgeraete-Verhalten und alte Clients beruecksichtigen.

LEG-03 bestaetigt ausserdem fehlendes timeout im alten webpush-Aufruf; dies
erweitert A-115 statt eines weiteren gleichartigen Befunds. A-011 ist damit
eine funktionale Konsolidierungsaufgabe, keine blosse Entfernung alter Dateien.

Naechster Schwerpunkt: Dokumentationsabgleich und Register der noch fehlenden
Betriebsnachweise. Scheduler-Konfiguration, reale Geraete, Sommerzeitgrenzen,
Shutdown-Verhalten und Restore-Probe bleiben ausdruecklich offen.
