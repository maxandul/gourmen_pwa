#!/usr/bin/env python3
"""
Fügt die Spalte 'beitritt' (DATE) zur lokalen SQLite-DB hinzu,
falls sie noch nicht existiert. Nutzt standardmäßig instance/app.db.
"""

import os
import sqlite3
from pathlib import Path


def resolve_db_path(project_root: Path) -> Path:
    # Optional Umgebungsvariable
    env_path = os.environ.get("DB_PATH")
    if env_path:
        return Path(env_path)

    # Bevorzugt instance/app.db, ansonsten gourmen_dev.db falls vorhanden
    default = project_root / "instance" / "app.db"
    alt = project_root / "instance" / "gourmen_dev.db"

    if default.exists():
        return default
    if alt.exists():
        return alt
    return default  # Fallback für Fehlermeldung


def main():
    project_root = Path(__file__).resolve().parent.parent
    db_path = resolve_db_path(project_root)

    if not db_path.exists():
        raise SystemExit(f"[WARN] SQLite-DB nicht gefunden unter {db_path}. DB_PATH setzen oder Datei anlegen.")

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info('members');")
        cols = {row[1] for row in cur.fetchall()}
        if "beitritt" in cols:
            print("[OK] Spalte 'beitritt' existiert bereits, nichts zu tun.")
            return

        cur.execute("ALTER TABLE members ADD COLUMN beitritt DATE;")
        conn.commit()
        print("[OK] Spalte 'beitritt' wurde hinzugefügt (TYPE DATE).")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

