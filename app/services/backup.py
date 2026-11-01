"""Export / import data MySQL ke file JSON (untuk cadangan & Google Drive)."""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

from config import BACKUP_PATH, MYSQL_DATABASE
from app.db import db_session, get_connection, init_db

TABLES = [
    "users",
    "kategori",
    "lokasi",
    "barang",
    "peminjaman",
    "sync_log",
    "app_meta",
]


def export_to_json(path: Path | None = None) -> Path:
    target = Path(path or BACKUP_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)

    conn = get_connection()
    payload = {
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "database": MYSQL_DATABASE,
        "tables": {},
    }
    try:
        for table in TABLES:
            rows = conn.execute(f"SELECT * FROM `{table}`").fetchall()
            payload["tables"][table] = [dict(r) for r in rows]
    finally:
        conn.close()

    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def import_from_json(path: Path | None = None, make_local_bak: bool = True) -> dict:
    source = Path(path or BACKUP_PATH)
    if not source.exists():
        raise FileNotFoundError(f"File backup tidak ditemukan: {source}")

    if make_local_bak:
        bak = BACKUP_PATH.with_suffix(".json.bak")
        try:
            export_to_json(bak)
        except Exception:
            pass

    data = json.loads(source.read_text(encoding="utf-8"))
    tables = data.get("tables") or {}

    # Pastikan struktur tabel ada
    init_db()

    with db_session() as conn:
        conn.execute("SET FOREIGN_KEY_CHECKS = 0")
        for table in reversed(TABLES):
            conn.execute(f"TRUNCATE TABLE `{table}`")

        # Urutan insert mengikuti dependency FK
        for table in TABLES:
            rows = tables.get(table) or []
            if not rows:
                continue
            cols = list(rows[0].keys())
            placeholders = ", ".join(["%s"] * len(cols))
            col_sql = ", ".join(f"`{c}`" for c in cols)
            sql = f"INSERT INTO `{table}` ({col_sql}) VALUES ({placeholders})"
            for row in rows:
                values = [row.get(c) for c in cols]
                conn.execute(sql, values)

        conn.execute("SET FOREIGN_KEY_CHECKS = 1")

    return {
        "message": f"Restore MySQL berhasil dari {source.name}",
        "tables": {t: len(tables.get(t) or []) for t in TABLES},
    }
