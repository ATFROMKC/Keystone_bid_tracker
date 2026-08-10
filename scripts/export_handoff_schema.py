"""One-shot: export BidTracker schema after init_db() into handoff/01-data-model/schema.sql"""
from __future__ import annotations

import importlib.util
import os
import sqlite3
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PY = ROOT / "keystone_bid_tracker" / "database.py"
OUT = ROOT / "handoff" / "01-data-model" / "schema.sql"


def main() -> None:
    spec = importlib.util.spec_from_file_location("database", DB_PY)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)

    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        db = mod.Database(path)
        db.init_db()
        conn = sqlite3.connect(path)
        rows = conn.execute(
            """
            SELECT type, name, sql
            FROM sqlite_master
            WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%'
            ORDER BY CASE type
                WHEN 'table' THEN 0
                WHEN 'index' THEN 1
                ELSE 2
            END, name
            """
        ).fetchall()

        lines = [
            "-- Keystone Bid Tracker schema export",
            "-- Generated from Database.init_db() (CREATE TABLE + ALTER migrations applied)",
            "-- Source of truth: keystone_bid_tracker/database.py",
            "",
        ]
        for type_, name, sql in rows:
            lines.append(f"-- {type_}: {name}")
            lines.append(sql.strip() + ";")
            lines.append("")

        lines.append("-- =============================================================================")
        lines.append("-- Effective columns (after ALTER migrations)")
        lines.append("-- =============================================================================")
        tables = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        for table in tables:
            lines.append(f"-- TABLE {table}")
            for _cid, col, ctype, notnull, dflt, pk in conn.execute(f"PRAGMA table_info({table})"):
                nn = " NOT NULL" if notnull else ""
                pkf = " PRIMARY KEY" if pk else ""
                df = f" DEFAULT {dflt}" if dflt is not None else ""
                lines.append(f"--   {col} {ctype}{nn}{df}{pkf}")
            lines.append("")

        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text("\n".join(lines), encoding="utf-8")
        print(f"Wrote {OUT} ({len(rows)} objects, {len(tables)} tables)")
        conn.close()
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


if __name__ == "__main__":
    main()
