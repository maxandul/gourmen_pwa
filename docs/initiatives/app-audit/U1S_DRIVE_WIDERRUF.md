# U1s / A-089: dauerhafter Drive-Widerruf

Stand: 12.10.2026. Lokaler Auftrag aus der Fortsetzung nach U1r.
Basis `7a2e93d`, Branch `codex/u1s-drive-access-revocation`. Keine Produktion.

## Technischer Vertrag vor Umsetzung

- Eine neue additive Tabelle speichert Drive-Aufgaben mit Mitglied, alter Adresse,
  konkretem Drive, Aktion, Status, Versuchen und sicheren Fehlercodes. Kein
  Bestandsdaten-Backfill, kein externer Aufruf aus der Migration. Migration separat.
- Adresswechsel und Deaktivierung erfassen den Widerruf in derselben Transaktion.
  Auch unverifizierte alte Adressen werden erfasst: ein früherer Invite kann
  bereits erfolgreich gewesen sein. Fehlende Konfiguration bleibt sichtbar offen.
- Verifikation erfasst auch den Invite dauerhaft. Neue Adresswechsel und
  Deaktivierung verwerfen ausstehende Invites. Deaktivierung entwertet Google-
  Links und Verifikationsstatus; nach Reaktivierung ist neue Verifikation nötig.
- Mitgliedssperre serialisiert Ausgabe, Verbrauch, Deaktivierung und Abarbeitung.
  Ein Auftrag hält diese Sperre bis nach seinem externen Aufruf und DB-Commit.
  Innerhalb dieser Transaktion kein selbst committender Audit-Helfer.
  Vor Invites immer den aktuellen Aktiv-/Adress-/Verifikationsstand prüfen.
- Widerrufe haben Vorrang vor Invites; ein Fehler blockiert spätere Einladungen.
  Mehrmaliger Wechsel A → B → A erhält die alten Widerrufe und lädt A erst nach
  deren Abschluss neu ein. Erfolgreiche Teilschritte bleiben einzeln gespeichert.
- Drive-Permissions vollständig paginieren, nur direkte User-Freigaben der
  gespeicherten Adresse bearbeiten. Fehlende Permission nach erfolgreicher Liste
  zählt als erledigt; Delete-404 erst nach erneuter erfolgreicher Liste. Fehler
  beim Zugriff auf das Drive (auch 404) sind kein erfolgreicher Widerruf.
- Wiederholung nach API-Erfolg/DB-Fehler ist idempotent: Grant prüft vorhandene
  Freigabe, Revoke prüft Abwesenheit. Keine neuen Benachrichtigungsmails von Drive.
- Adminübersicht zeigt offene Aufträge unabhängig vom Feature-Flag. Wiederholung
  nur als CSRF-geschützter POST eines aktiven Admins; kein GET mit API-Mutation.
  Ein erster Versuch folgt nach dem lokalen Commit. Bei Fehlern bleibt die
  Adminaufgabe erhalten, ohne Erfolgsbehauptung oder rohe API-Fehlertexte.

## Umsetzung und lokaler Nachweis

`DriveAccessTask` und `DriveAccessService` implementieren den Vertrag. Alte
Drive-Ziele erfolgreicher/ausstehender Einladungen bleiben bei späterem
Konfigurationswechsel erhalten. Ein Auftrag ohne Drive-ID bleibt offen; Admins
können ihn mit einer expliziten Checkbox dem konfigurierten Vereins-Drive zuordnen.
Bereits gespeicherte IDs werden dadurch nie umgebogen. Fehlgeschlagene Schritte
werden einzeln wiederholt; ein abgeschlossener Schritt wird nicht erneut ausgeführt.
Admin-Wiederholungen protokollieren den tatsächlichen Admin als Akteur.
Kein neuer Cron, keine neue Dependency, kein Mail-Wiederaufnahmevertrag.

Der Transport prüft alle Seiten der Permission-Liste und bestätigt nach dem
Löschen die Abwesenheit. Referenzen: [Google permissions.list](https://developers.google.com/workspace/drive/api/reference/rest/v3/permissions/list)
und [permissions.delete](https://developers.google.com/workspace/drive/api/reference/rest/v3/permissions/delete).
Die bestehenden Legacy-Transporthelfer bleiben verfügbar, werden vom
Verifikationsablauf aber nicht mehr direkt aufgerufen.

- Gesamtlauf: **578 bestanden**, 5282 Warnungen, 318,50 Sekunden. Danach vier
  zusätzliche gezielte Fälle für gültigen CSRF-POST/Audit, unveränderte Adresse,
  Deaktivierungs-Commitfehler und Erhalt fremder Aufgaben/Token ergänzt.
- Abschliessender gezielter Lauf: **69 bestanden**, 888 Warnungen, 12,74 Sekunden:
  neue Services/Transport/Migration sowie U1o- und U1p-Regressionsdateien. Darin
  **35 neue A-089-Fälle**; U1o-Erwartung angepasst: eine zwischenzeitlich veraltete
  Einladung wird jetzt verworfen, statt noch den alten Snapshot einzuladen.
- Tests nutzen den vorhandenen isolierenden Teststarter: SQLite im Speicher,
  dotenv deaktiviert, ausgehende Sockets gesperrt, ausschliesslich synthetische
  Konten und ersetzte API. Keine lokalen Bestandsdatenbanken geöffnet.
- Migration `a08920261012` über `a4b7c2d9e015`: nur neue Tabelle mit Constraints,
  FK und Index. Upgrade → Downgrade → Upgrade mit Alembic Operations auf eigener
  In-Memory-DB geprüft; bestehender Mitgliedsdatensatz bleibt erhalten, einzelner
  Alembic-Head bestätigt. Kein vollständiger historischer Migrationslauf und
  kein PostgreSQL-Nachweis. Downgrade löscht Aufgabenhistorie: vor produktivem
  Einsatz gesondertes Betriebs-/Backupvorgehen, nicht mit offenen Aufgaben ausführen.
- Browserprüfung gegen separate lokale In-Memory-Vorschau: 390px hell, 320px
  hell/dunkel, 768px dunkel, 1440px hell/dunkel. Lange Adresse, offene/fehlgeschlagene
  Aufgabe, fehlende Drive-Zuordnung und Aktionsumbruch sichtbar geprüft. Keine
  horizontale Seitenüberbreite; bei 320px auch Buttons ohne internen Überlauf.
  Theme-Wechsel über Tastatur bestätigt. Keine vollständige Geräteabnahme.
- Bestehende Cards/Formulare/Buttons wiederverwendet, keine neuen CSS-Klassen.
  PWA-Version 3.16.4, Fingerprint `pwa.bd0c7e99.js`; nur geändertes PWA-Asset
  fingerprinted, fremde Hashkopien erhalten. Kein UI-Gesamtumbau.

Migration separat lokal gesichert in `4538a79`; übrige Umsetzung folgt im
eigenen Feature-Commit. PWA-Version, Hash, identische Quellkopie und Template-
Verweis zusätzlich geprüft. Die neue Hashkopie übernimmt unveränderte vorhandene
Leerzeichen am Zeilenende aus `pwa.js`; diese sind kein neuer Quellcodefehler.
Kein Push, Merge auf master, Deploy, Produktionszugriff oder Schlüsselwechsel.

## Grenzen und ausstehende Nachweise

SQLite mit synthetischen Daten und ersetzter Drive-API; PostgreSQL-Sperren,
echtes Drive und Geräte/PWA separat. Bestehende Gruppen-/Domain-
Freigaben und individuell geteilte Dateien ausserhalb der Shared-Drive-
Mitgliedschaft sind kein Gegenstand dieses Auftrags. Historisch verlorene alte
Adressen lassen sich ohne externe Bestandsaufnahme nicht rekonstruieren.
Direkte DB-/Importänderungen umgehen die App-Verträge. Eine verteilte Transaktion
mit Google existiert nicht; insbesondere extern noch laufende Requests nach
Transportabbruch brauchen echte Integrationsabnahme. Kein vollständiger U1-Abschluss.
Die App lässt weiterhin dieselbe Google-Adresse an mehreren Konten zu (bereits
offener Zugangsvertrag aus AUTH_REVIEW). Die externe Freigabe gehört der Adresse;
ein Widerruf kann damit mehrere solche Konten betreffen. Diese Zuordnung ist vor
Veröffentlichung zu klären; es wird kein neues Modell für geteilte Konten eingeführt.
Nächste offene U1-Pakete bleiben A-076/Pflichtwechsel sowie allgemeiner
Sitzungs-/Gerätewiderruf; kein weiterer Auftrag oder Gesamtabnahme abgeleitet.
