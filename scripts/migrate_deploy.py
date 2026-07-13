#!/usr/bin/env python3
"""Alembic upgrade fuer Railway preDeploy (mit PostgreSQL Advisory Lock).

Verhindert parallele Migrationen wenn web und cron gleichzeitig deployen.
"""
from __future__ import annotations

import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask_migrate import upgrade
from sqlalchemy import text

from backend.app import create_app
from backend.extensions import db

# Feste Lock-ID fuer Gourmen PWA DB-Migrationen (nur ein Deploy gleichzeitig).
_MIGRATION_LOCK_ID = 0x474F55524D454E00


def main() -> int:
    database_url = os.environ.get("DATABASE_URL") or ""
    if not database_url.startswith(("postgres://", "postgresql://", "postgresql+")):
        print("Keine PostgreSQL DATABASE_URL — ueberspringe db upgrade")
        return 0

    app = create_app("production")
    with app.app_context():
        with db.engine.connect() as lock_conn:
            lock_conn.execute(
                text("SELECT pg_advisory_lock(:lock_id)"),
                {"lock_id": _MIGRATION_LOCK_ID},
            )
            lock_conn.commit()
        try:
            print("Starte flask db upgrade …")
            upgrade()
            print("DB upgrade erfolgreich")
        except Exception as exc:
            print(f"DB upgrade fehlgeschlagen: {exc}", file=sys.stderr)
            traceback.print_exc()
            return 1
        finally:
            with db.engine.connect() as lock_conn:
                lock_conn.execute(
                    text("SELECT pg_advisory_unlock(:lock_id)"),
                    {"lock_id": _MIGRATION_LOCK_ID},
                )
                lock_conn.commit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
