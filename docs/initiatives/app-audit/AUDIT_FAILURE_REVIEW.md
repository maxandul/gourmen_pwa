# Gemeinsames Aktivitaetsprotokoll – Fehlerreichweite

Stand 2026-09-21. Fuenf isolierte Gruppen ausserhalb der Dokumentverwaltung.
[AUDIT_FAILURE_ROUTE_CHECKS.json](AUDIT_FAILURE_ROUTE_CHECKS.json), reproduzierbar
mit check_audit_failure_routes.py. Originale Flask-Routen und Audit-Writer;
synthetischer OperationalError im AuditEvent-Insert, SQLite im Speicher.

| Fall | Antwort im Test | Dauerhafter Zustand |
|---|---|---|
| Login ohne next | PendingRollbackError bei nachfolgendem Zugriff auf needs_password_change | Kein Login-Cookie gespeichert, Audit fehlt. |
| Login mit lokalem next | 302 zum angegebenen Ziel | Session authentifiziert, Audit fehlt. |
| RSVP, dann Wiederholung nach Erholung | Erster Request PendingRollbackError, zweiter 302 | Erst Teilnahme true committed, nach Wiederholung false; ein Audit fuer zweiten Request. |
| Kalender aktivieren | 201 | Feed aktiviert, Audit fehlt. |
| Zukuenftiges synthetisches Event loeschen | PendingRollbackError | Event erhalten; Auditfehler tritt vor Loeschung auf. |

A-137 betrifft somit mehrere Originalrouten, aber nicht jeder Aufrufer bricht
sichtbar ab: Nachfolgende ORM-Zugriffe und Transaktionsreihenfolge entscheiden.
Keine pauschale Behauptung, die Anmeldung oder alle Fachaktionen seien defekt.
A-138 erfasst separat das nicht wiederholungssichere RSVP-Toggle: Beheben des
Auditfehlers allein sichert auch andere verlorene Antworten nicht ab.

Empfehlung: Audit-Transaktionsgrenze zentral definieren und Aufrufer mit noch
offenen Fachaenderungen gesondert pruefen. Expliziten Teilnahme-Zielzustand
statt blossem Umschalten an den Server senden. Erfolgreich gespeicherte Aktion,
fehlendes Protokoll und tatsaechlich fehlgeschlagene Aktion unterscheidbar machen.

Der erste Login-Test erreichte mit example.test den vorgesehenen Fehlerpfad
nicht (Formular blieb bei 200). Nach Wechsel auf synthetische example.com-
Adresse liefen alle fuenf Gruppen bis zum injizierten Auditfehler. Keine echte
Adresse kontaktiert, keine Mail gesendet und keine Zugangsdaten ausgegeben.

Grenzen: Testing propagiert Exceptions; kein beobachteter Produktions-HTTP-Body.
CSRF/Rate-Limits deaktiviert. Frischer App-Kontext pro Request/Zustandsabfrage,
kein mitwandernder Flask-Login-Cache. Weitere Audit-Aufrufer, MFA/Admin-Flows,
PostgreSQL, Request-Abbruch und echte Nebenlaeufigkeit bleiben offen.

## Aufruferinventar und Transaktionsgrenze

[AUDIT_CALL_INVENTORY.json](AUDIT_CALL_INVENTORY.json) erfasst 64 direkte
Aufrufstellen per Python-AST: Admin 9, Auth 13, BillBro 13, Events 4, Member 7,
Notifications 2, Drive-Service 16. Jede Zeile enthaelt Funktion, Aktion und
Quellzeile. Status bewusst nur inventarisiert: kein vollstaendiger Verhaltens-
oder Erreichbarkeitsnachweis fuer alle 64 Aufrufe und keine Alias-Aufloesung.

Drei gezielte Originalhelfer-Proben in
[AUDIT_TRANSACTION_CHECKS.json](AUDIT_TRANSACTION_CHECKS.json),
check_audit_transactions.py:

| Zustand vor Protokollierung | Zustand nach anschliessendem aeusserem Rollback |
|---|---|
| Keine offene Fachaenderung, Audit erfolgreich | Mitglied unveraendert, ein Audit gespeichert. |
| Ungespeicherte Namensaenderung, Audit erfolgreich | Name und Audit bereits dauerhaft gespeichert; aeusseres Rollback nimmt Namen nicht zurueck. |
| Ungespeicherte Namensaenderung, Audit-Insert scheitert | Nach explizitem Rollback alter Name und kein Audit. |

Das ist ein nachgewiesener Transaktionseffekt, fuer sich kein Beweis einer
unbeabsichtigten produktiven Mitglieder-Aenderung. Quellcodeabgleich zeigt
unterschiedliche Nutzung: Die Eventbearbeitung committet vor dem Audit;
Admin-Mitgliederanlage legt vor ihren beiden Audit-Aufrufen einen
Onboarding-Token in derselben Session an und hat erst danach einen eigenen
Commit. Notifications gibt nach dem Audit in den betrachteten Erfolgszweigen
direkt JSON zurueck. BillBro mischt Service-Aufrufe und eigene Commits; deren
saemtliche Transaktionspfade sind hier nicht verifiziert.

Konsequenz fuer A-137: vor Umbau festlegen, ob Protokoll und Fachaenderung
gemeinsam atomar oder separat gespeichert werden. Die Entscheidung je Ablauf
dokumentieren; danach gezielte Fehlerproben an den betroffenen Aufrufern.
Ungeprueftes Entfernen des Helfer-Commits oder globales Rollback kann andere
offene Aenderungen beeinflussen. Drei weitere Gruppen, weiterhin 138 Befunde.
Keine App-Aenderungen, keine echten Mitglieder-/Token-/Mail-Aktionen.

## Mitgliederanlage: konkrete Transaktionsfolgen vom 2026-09-28

Fuenf Originalrouten-Proben in ONBOARDING_FAILURE_CHECKS.json. Erster Audit-
Fehler laesst nur das zuvor gespeicherte Konto uebrig; zweiter Audit-Fehler
laesst Konto, Aktivierungstoken und ersten Protokolleintrag uebrig. Beide
Requests enden in Testing mit PendingRollbackError. A-137 damit um einen
konkreten Admin-Aufrufer erweitert, A-139 zur vorgezogenen Versandbeauftragung.
Mail vollstaendig abgefangen, keine echten Mitglieder oder Nachrichten.

Aktivierung ergaenzt: ACTIVATION_BOUNDARY_CHECKS.json zeigt bei Auditfehler
bereits gespeichertes Passwort/verbrauchten Token, aber gescheiterte anschliessende
Anmeldung. Dies ist ein weiterer konkreter A-137-Aufrufer; positive Kontrollen
fuer Ablauf, Zweck, deaktivierte Konten und normale Wiederverwendung in AUTH_REVIEW.md.
