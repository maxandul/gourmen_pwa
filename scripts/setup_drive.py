#!/usr/bin/env python3
"""Idempotentes Setup-Script fuer das Vereins-Drive.

Authoritative Spezifikation: ``docs/capabilities/drive.md`` (Sektion 17.1).

Aufgaben:

1. Service-Account-Authentifizierung gegen `GOOGLE_DRIVE_ID` pruefen.
2. Top-Level-Folders im Shared Drive idempotent anlegen
   (acht Aktiv-Kategorien + ``99_Archiv``).
3. Folder-IDs als Liste ausgeben, damit sie ggf. dokumentiert werden koennen.
4. Optional alle Members mit verifizierter ``google_email`` als
   ``content_manager`` ins Shared Drive einladen (``--invite-members``).

Nutzung lokal::

    python scripts/setup_drive.py
    python scripts/setup_drive.py --invite-members

Im Railway-Web-Service::

    railway ssh --project ... --service ... \\
        "/opt/venv/bin/python scripts/setup_drive.py"

Voraussetzungen:

* ``GOOGLE_SERVICE_ACCOUNT_KEY`` (Base64-encodiertes Service-Account-JSON)
  ist als ENV-Variable gesetzt.
* ``GOOGLE_DRIVE_ID`` zeigt auf das Vereins-Shared-Drive und der
  Service-Account hat dort die Rolle ``content_manager`` (oder hoeher).

Das Script ist idempotent: mehrfaches Ausfuehren erzeugt keine Duplikate.
"""

from __future__ import annotations

import argparse
import logging
import sys

# Sicherstellen, dass der Repo-Root im sys.path ist (Script-Aufruf direkt).
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app import create_app  # noqa: E402
from backend.extensions import db  # noqa: E402
from backend.models.member import Member  # noqa: E402
from backend.services.drive_storage import (  # noqa: E402
    DriveError,
    DriveNotConfiguredError,
    DriveStorageService,
)


logger = logging.getLogger("setup_drive")


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    )


def _ensure_folder_structure() -> dict[str, str]:
    """Erstellt/prueft die Top-Level-Folders im Shared Drive."""
    print("\n[1/3] Pruefe Folder-Struktur im Shared Drive ...")
    folders = DriveStorageService.initialize_folder_structure()
    print(f"      OK – {len(folders)} Folders verfuegbar:")
    for name, folder_id in folders.items():
        print(f"        - {name:30s}  ->  {folder_id}")
    return folders


def _verify_drive_access(drive_id: str) -> None:
    """Prueft, dass der Service-Account das Shared Drive sehen kann."""
    print("\n[2/3] Pruefe Service-Account-Zugriff aufs Shared Drive ...")
    drive = DriveStorageService._build_drive()  # noqa: SLF001
    info = (
        drive.drives()
        .get(driveId=drive_id, fields="id, name, capabilities")
        .execute()
    )
    print(
        f"      OK – Drive «{info.get('name')}» (ID {info.get('id')}) "
        "ist erreichbar."
    )
    caps = info.get("capabilities") or {}
    if not caps.get("canAddChildren", False):
        print(
            "      WARN – Service-Account hat keine Berechtigung, Inhalte "
            "anzulegen. Ueberpruefe die Drive-Mitgliedschaft "
            "(Rolle 'Content-Manager' oder hoeher noetig)."
        )


def _invite_verified_members() -> None:
    """Lade alle Members mit verifizierter Google-Adresse ins Drive ein."""
    print("\n[3/3] Lade verifizierte Members ins Vereins-Drive ein ...")
    members = (
        Member.query.filter(
            Member.is_active.is_(True),
            Member.google_email_verified.is_(True),
            Member.google_email.isnot(None),
        )
        .order_by(Member.id.asc())
        .all()
    )
    if not members:
        print("      (Keine verifizierten Members gefunden – nichts zu tun.)")
        return

    invited = 0
    skipped = 0
    failed = 0
    for member in members:
        try:
            DriveStorageService.invite_member_to_drive(member)
            invited += 1
            print(f"      OK   {member.google_email}")
        except DriveError as exc:
            failed += 1
            print(f"      FAIL {member.google_email}: {exc}")
        except Exception as exc:  # pragma: no cover – defensive
            failed += 1
            print(f"      FAIL {member.google_email}: {exc}")

    db.session.commit()
    print(
        "      Zusammenfassung: "
        f"{invited} eingeladen, {skipped} uebersprungen, {failed} Fehler."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--invite-members",
        action="store_true",
        help=(
            "Lade nach dem Folder-Setup alle Members mit verifizierter "
            "google_email als 'content_manager' ins Vereins-Drive ein."
        ),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose Logging (DEBUG-Level fuer alle Module).",
    )
    args = parser.parse_args(argv)

    _setup_logging(args.verbose)

    print("=" * 72)
    print("Gourmen Drive – Setup")
    print("=" * 72)

    app = create_app()
    with app.app_context():
        try:
            drive_id = DriveStorageService._get_drive_id()  # noqa: SLF001
        except DriveNotConfiguredError as exc:
            print(f"\nFEHLER: {exc}")
            print(
                "        Bitte GOOGLE_DRIVE_ID und GOOGLE_SERVICE_ACCOUNT_KEY "
                "als ENV-Variablen setzen."
            )
            return 2

        try:
            _verify_drive_access(drive_id)
            _ensure_folder_structure()
            if args.invite_members:
                _invite_verified_members()
            else:
                print(
                    "\n[3/3] Member-Invites uebersprungen "
                    "(Flag --invite-members nicht gesetzt)."
                )
        except DriveNotConfiguredError as exc:
            print(f"\nFEHLER (Konfiguration): {exc}")
            return 2
        except DriveError as exc:
            print(f"\nFEHLER (Drive-API): {exc}")
            return 3

    print("\nFertig. Setup ist idempotent – mehrfaches Ausfuehren ist sicher.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
