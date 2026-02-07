"""Tests for SQL migration scripts."""

import sqlite3
import subprocess
import sys
from pathlib import Path


def create_legacy_schema(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(
            """
            CREATE TABLE persons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL
            );

            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                FOREIGN KEY (person_id) REFERENCES persons(id)
            );
            """
        )
        conn.commit()
    finally:
        conn.close()


def test_apply_sql_migrations_adds_receipt_tables(tmp_path):
    db_path = tmp_path / 'legacy.db'
    create_legacy_schema(db_path)

    result = subprocess.run(
        [
            sys.executable,
            'scripts/apply_sql_migrations.py',
            '--db',
            str(db_path),
            '--migrations-dir',
            'migrations',
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    assert 'Applying 001_receipts.sql' in result.stdout

    conn = sqlite3.connect(db_path)
    try:
        tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }
        assert 'schema_migrations' in tables
        assert 'tax_receipts' in tables
        assert 'tax_receipt_items' in tables

        applied = conn.execute(
            "SELECT version FROM schema_migrations WHERE version = '001_receipts'"
        ).fetchone()
        assert applied is not None
    finally:
        conn.close()


def test_apply_sql_migrations_is_idempotent(tmp_path):
    db_path = tmp_path / 'legacy.db'
    create_legacy_schema(db_path)

    cmd = [
        sys.executable,
        'scripts/apply_sql_migrations.py',
        '--db',
        str(db_path),
        '--migrations-dir',
        'migrations',
    ]

    first = subprocess.run(cmd, check=False, text=True, capture_output=True)
    second = subprocess.run(cmd, check=False, text=True, capture_output=True)

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    assert 'No pending migrations.' in second.stdout
