# U2-09: Konfliktsicheres Bereinigungs-Undo

## Vertrag vor Code

A-029: Undo darf nur den eigenen unveraenderten Nachzustand rueckgaengig
machen. Unter Event-/Teilnahmesperre wird ein Fingerabdruck aller gespeicherten
Teilnahmefelder und des Eventstands mit dem nach erfolgreicher Bereinigung
gesicherten Fingerabdruck verglichen. Alt-Sessions ohne Nachweis verfallen.
Spaetere BillBro-Eingaben, Anwesenheitskorrekturen, Bewertungen, Forderungen
oder Buchungen sperren den einfachen Undo-Weg. Kein Loeschen einer inzwischen
anderweitig verwendeten Zeile. Eventzugriff, aktives Mitglied und vergangenes
Event erneut pruefen. Ebenso keine einfache Bereinigungsmutation bereits
finanziell/mit BillBro oder Bewertung verwendeter Teilnahme.

Konflikt meldet unveraenderten Stand und verbraucht das veraltete Undo. Ein
technischer Commitfehler rollt zurueck und behaelt den Undo-Nachweis fuer
Wiederholung. Erfolgreiches Undo entfernt nur selbst angelegte einfache Zeile
oder stellt die vorherige Teilnahme/Antwortzeit her. Keine Migration.

## Lokaler Nachweis

18.10.2026: 25 Tests fuer Undo/Sichtbarkeit bestanden (616 Warnungen,
13.40 s). Mit originalem Wiederholungsweg nach Commitfehler und BillBro-
Betragsregressionen 67 Tests bestanden (712 Warnungen, 24.52 s).
Diff-Pruefung sauber. Kein Schema-/Template-/Assetwechsel.
Pruefungen enthalten Originalfolge Bereinigung -> Tipp CHF 104 -> Undo,
neue/alte Zeile, Austausch der Zeile, Mehrtab, Alt-Sitzung, Bewertung,
Forderung, Abrechnung, Anwesenheit, Rechteentzug und Commitfehler.
PostgreSQL-Nebenlaeufigkeit und Browserabnahme offen; keine externen Zugriffe.
