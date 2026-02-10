"""Tests for legacy DB import workflow."""

import sqlite3
import subprocess
import sys


def test_import_legacy_db_script_creates_fresh_schema_and_copies_data(tmp_path):
    source_db = tmp_path / 'legacy.db'
    target_db = tmp_path / 'fresh.db'

    source_conn = sqlite3.connect(str(source_db))
    try:
        source_conn.executescript(
            """
            CREATE TABLE persons (
                id INTEGER PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                address TEXT,
                notes TEXT,
                created_at TEXT,
                updated_at TEXT,
                deleted_at TEXT
            );

            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY,
                person_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                method TEXT NOT NULL,
                amount REAL NOT NULL,
                accepted_by TEXT NOT NULL,
                receipt INTEGER,
                memo TEXT,
                created_at TEXT,
                updated_at TEXT,
                deleted_at TEXT
            );

            INSERT INTO persons (id, first_name, last_name, email) VALUES
                (1, 'Alice', 'Wu', 'alice@example.com'),
                (2, 'Bob', 'Xi', 'bob@example.com');

            INSERT INTO transactions (id, person_id, date, method, amount, accepted_by, receipt) VALUES
                (11, 1, '2024-01-01', 'Cash', 20.0, 'Treasurer', 0),
                (12, 2, '2024-02-01', 'Credit', 35.0, 'Treasurer', 1);
            """
        )
        source_conn.commit()
    finally:
        source_conn.close()

    result = subprocess.run(
        [
            sys.executable,
            'scripts/import_legacy_db.py',
            '--source-db',
            str(source_db),
            '--target-db',
            str(target_db),
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    assert 'Imported 2 rows into persons' in result.stdout
    assert 'Imported 2 rows into transactions' in result.stdout

    target_conn = sqlite3.connect(str(target_db))
    try:
        people_count = target_conn.execute('SELECT COUNT(*) FROM persons').fetchone()[0]
        transaction_count = target_conn.execute('SELECT COUNT(*) FROM transactions').fetchone()[0]
        receipt_count = target_conn.execute('SELECT COUNT(*) FROM tax_receipts').fetchone()[0]
        receipt_item_count = target_conn.execute('SELECT COUNT(*) FROM tax_receipt_items').fetchone()[0]
    finally:
        target_conn.close()

    assert people_count == 2
    assert transaction_count == 2
    assert receipt_count == 0
    assert receipt_item_count == 0
