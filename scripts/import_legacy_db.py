"""Create a fresh database and import legacy persons/transactions data."""

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
    parser = argparse.ArgumentParser(description='Import legacy SQLite data into a fresh schema.')
    parser.add_argument('--source-db', required=True, type=Path, help='Path to old SQLite database file.')
    parser.add_argument('--target-db', required=True, type=Path, help='Path to new SQLite database file.')
    parser.add_argument(
        '--force',
        action='store_true',
        help='Overwrite target DB if it already exists.',
    )
    return parser.parse_args()


def copy_table_data(
    source_conn: sqlite3.Connection, target_conn: sqlite3.Connection, table_name: str
) -> tuple[int, int]:
    source_columns = [row[1] for row in source_conn.execute(f'PRAGMA table_info({table_name})').fetchall()]
    target_columns = [row[1] for row in target_conn.execute(f'PRAGMA table_info({table_name})').fetchall()]
    common_columns = [col for col in source_columns if col in target_columns]

    if not common_columns:
        return 0, 0

    select_sql = f"SELECT {', '.join(common_columns)} FROM {table_name}"
    rows = source_conn.execute(select_sql).fetchall()
    if not rows:
        return 0, len(common_columns)

    placeholders = ', '.join('?' for _ in common_columns)
    insert_sql = (
        f"INSERT INTO {table_name} ({', '.join(common_columns)}) VALUES ({placeholders})"
    )
    target_conn.executemany(insert_sql, rows)
    return len(rows), len(common_columns)


def write_temp_config(target_db: Path) -> Path:
    target_db = target_db.resolve()
    backup_path = target_db.parent / 'backups'

    contents = f"""from pathlib import Path

SQLALCHEMY_DATABASE_PATH = Path(r'{target_db}')
SQLALCHEMY_DATABASE_URI = f"sqlite:///{{SQLALCHEMY_DATABASE_PATH.absolute()}}"
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_BACKUP_PATH = Path(r'{backup_path.resolve()}')
ORG = 'Unknown organisation'
TREASURER = 'Unknown treasurer'
TREASURER_NAME = 'Unknown treasurer'
TAX_YEAR = 2024
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
    from app.models.person import Person
    from app.models.tax_receipt import TaxReceipt, TaxReceiptItem
    from app.models.transaction import Transaction

    temp_config = write_temp_config(target_db)
    try:
        backend = create_app(temp_config)
        with backend.app_context():
            _ = (Person, Transaction, TaxReceipt, TaxReceiptItem)
            db.drop_all()
            db.create_all()
    finally:
        temp_config.unlink(missing_ok=True)


def main() -> int:
    args = parse_args()
    source_db = args.source_db.resolve()
    target_db = args.target_db.resolve()

    if not source_db.exists():
        raise FileNotFoundError(f'Source DB not found: {source_db}')

    if target_db.exists():
        if not args.force:
            raise FileExistsError(
                f'Target DB already exists: {target_db}. Use --force to overwrite.'
            )
        target_db.unlink()

    target_db.parent.mkdir(parents=True, exist_ok=True)
    create_empty_schema(target_db)

    source_conn = sqlite3.connect(str(source_db))
    target_conn = sqlite3.connect(str(target_db))
    try:
        target_conn.execute('PRAGMA foreign_keys = OFF')
        target_conn.execute('BEGIN')

        people_rows, _ = copy_table_data(source_conn, target_conn, 'persons')
        transactions_rows, _ = copy_table_data(source_conn, target_conn, 'transactions')

        target_conn.commit()
    except Exception:
        target_conn.rollback()
        raise
    finally:
        source_conn.close()
        target_conn.close()

    print(f'Imported {people_rows} rows into persons')
    print(f'Imported {transactions_rows} rows into transactions')
    print(f'New database ready: {target_db}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
