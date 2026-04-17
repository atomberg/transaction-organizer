"""Import legacy persons/transactions into the current donor-family schema."""

from __future__ import annotations

import argparse
import sqlite3
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Import legacy SQLite data into a fresh donor-family schema.'
    )
    parser.add_argument('--source-db', required=True, type=Path, help='Path to old SQLite database file.')
    parser.add_argument('--target-db', required=True, type=Path, help='Path to new SQLite database file.')
    parser.add_argument('--force', action='store_true', help='Overwrite target DB if it already exists.')
    return parser.parse_args()


def table_columns(conn: sqlite3.Connection, table_name: str) -> list[str]:
    rows = conn.execute(f'PRAGMA table_info({table_name})').fetchall()
    return [row[1] for row in rows]


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def write_temp_config(target_db: Path) -> Path:
    target_db = target_db.resolve()
    backup_path = target_db.parent / 'backups'
    contents = f"""from pathlib import Path

SQLALCHEMY_DATABASE_PATH = Path(r'{target_db}')
SQLALCHEMY_DATABASE_URI = f"sqlite:///{{SQLALCHEMY_DATABASE_PATH.absolute()}}"
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_BACKUP_PATH = Path(r'{backup_path.resolve()}')
ORGANISATION_NAME = 'Unknown organisation'
TREASURER_NAME = 'Unknown treasurer'
TAX_YEAR = 2026
"""
    with tempfile.NamedTemporaryFile(
        mode='w',
        prefix='migration_config_',
        suffix='.py',
        delete=False,
        encoding='utf-8',
    ) as handle:
        handle.write(contents)
        return Path(handle.name)


def create_empty_schema(target_db: Path) -> None:
    from app import create_app, db
    from app.models.family import Family, FamilyMember
    from app.models.person import Person
    from app.models.tax_receipt import TaxReceipt, TaxReceiptItem
    from app.models.transaction import Transaction

    temp_config = write_temp_config(target_db)
    try:
        backend = create_app(temp_config)
        with backend.app_context():
            _ = (Person, Transaction, TaxReceipt, TaxReceiptItem, Family, FamilyMember)
            db.drop_all()
            db.create_all()
    finally:
        temp_config.unlink(missing_ok=True)


def import_persons_and_families(source_conn: sqlite3.Connection, target_conn: sqlite3.Connection) -> dict[str, int]:
    source_person_columns = set(table_columns(source_conn, 'persons'))
    required = {'id', 'first_name', 'last_name'}
    missing = sorted(required.difference(source_person_columns))
    if missing:
        raise ValueError(f'Legacy persons table is missing required columns: {missing}')

    rows = source_conn.execute('SELECT * FROM persons ORDER BY id ASC').fetchall()
    people_count = 0
    family_count = 0
    membership_count = 0

    for row in rows:
        record = dict(row)
        person_id = record['id']
        first_name = record['first_name']
        last_name = record['last_name']
        address = record.get('address')
        notes = record.get('notes')
        created_at = record.get('created_at')
        updated_at = record.get('updated_at')
        deleted_at = record.get('deleted_at')

        target_conn.execute(
            """
            INSERT INTO persons (
                id, first_name, last_name, phone, email, address, notes, created_at, updated_at, deleted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                person_id,
                first_name,
                last_name,
                record.get('phone'),
                record.get('email'),
                address,
                None,
                created_at,
                updated_at,
                deleted_at,
            ),
        )
        people_count += 1

        target_conn.execute(
            """
            INSERT INTO families (
                id, display_name, address, notes, created_at, updated_at, deleted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                person_id,
                f'{last_name} Household',
                address,
                notes,
                created_at,
                updated_at,
                deleted_at,
            ),
        )
        family_count += 1

        target_conn.execute(
            """
            INSERT INTO family_members (
                family_id, person_id, created_at, updated_at, deleted_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                person_id,
                person_id,
                created_at,
                updated_at,
                deleted_at,
            ),
        )
        membership_count += 1

    return {
        'persons': people_count,
        'families': family_count,
        'family_members': membership_count,
    }


def import_transactions(source_conn: sqlite3.Connection, target_conn: sqlite3.Connection) -> dict[str, int]:
    if not table_exists(source_conn, 'transactions'):
        return {'transactions': 0}

    source_transaction_columns = set(table_columns(source_conn, 'transactions'))
    required = {'id', 'person_id', 'date', 'method', 'amount'}
    missing = sorted(required.difference(source_transaction_columns))
    if missing:
        raise ValueError(f'Legacy transactions table is missing required columns: {missing}')

    rows = source_conn.execute('SELECT * FROM transactions ORDER BY id ASC').fetchall()
    txn_count = 0
    for row in rows:
        record = dict(row)
        memo_text = (
            str(record.get('memo')).strip()
            if record.get('memo') is not None and str(record.get('memo')).strip()
            else None
        )
        accepted_text = (
            str(record.get('accepted_by')).strip()
            if record.get('accepted_by') is not None and str(record.get('accepted_by')).strip()
            else None
        )
        combined_memo = (
            f'{memo_text} {accepted_text}'
            if memo_text and accepted_text
            else memo_text or accepted_text
        )
        target_conn.execute(
            """
            INSERT INTO transactions (
                id, person_id, date, method, amount, receipt, memo, created_at, updated_at, deleted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record['id'],
                record['person_id'],
                record['date'],
                record['method'],
                record['amount'],
                record.get('receipt', 0) or 0,
                combined_memo,
                record.get('created_at'),
                record.get('updated_at'),
                record.get('deleted_at'),
            ),
        )
        txn_count += 1
    return {'transactions': txn_count}


def main() -> int:
    args = parse_args()
    source_db = args.source_db.resolve()
    target_db = args.target_db.resolve()

    if not source_db.exists():
        raise FileNotFoundError(f'Source DB not found: {source_db}')
    if target_db.exists():
        if not args.force:
            raise FileExistsError(f'Target DB already exists: {target_db}. Use --force to overwrite.')
        target_db.unlink()

    target_db.parent.mkdir(parents=True, exist_ok=True)
    create_empty_schema(target_db)

    source_conn = sqlite3.connect(str(source_db))
    target_conn = sqlite3.connect(str(target_db))
    source_conn.row_factory = sqlite3.Row
    target_conn.row_factory = sqlite3.Row

    try:
        target_conn.execute('PRAGMA foreign_keys = ON')
        target_conn.execute('BEGIN')

        person_stats = import_persons_and_families(source_conn, target_conn)
        transaction_stats = import_transactions(source_conn, target_conn)

        target_conn.commit()
    except Exception:
        target_conn.rollback()
        raise
    finally:
        source_conn.close()
        target_conn.close()

    print(f"Imported {person_stats['persons']} persons")
    print(f"Created {person_stats['families']} families")
    print(f"Created {person_stats['family_members']} family memberships")
    print(f"Imported {transaction_stats['transactions']} transactions")
    print(f'New database ready: {target_db}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
