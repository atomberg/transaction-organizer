"""Apply SQL migrations to a SQLite database file."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Apply SQL migrations to a SQLite database.')
    parser.add_argument('--db', required=True, type=Path, help='Path to SQLite database file.')
    parser.add_argument(
        '--migrations-dir',
        type=Path,
        default=Path('migrations'),
        help='Directory containing numbered .sql migration files.',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show migrations that would be applied without modifying the database.',
    )
    return parser.parse_args()


def migration_version(path: Path) -> str:
    return path.stem


def ensure_migration_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()


def get_applied_versions(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute('SELECT version FROM schema_migrations').fetchall()
    return {row[0] for row in rows}


def get_migration_files(migrations_dir: Path) -> list[Path]:
    files = sorted(path for path in migrations_dir.glob('[0-9][0-9][0-9]_*.sql') if path.is_file())
    if not files:
        raise FileNotFoundError(f'No migration files found in {migrations_dir}')
    return files


def apply_migration(conn: sqlite3.Connection, path: Path) -> None:
    sql = path.read_text(encoding='utf-8')
    conn.executescript(sql)
    conn.commit()


def main() -> int:
    args = parse_args()

    if not args.db.exists():
        raise FileNotFoundError(f'Database does not exist: {args.db}')
    if not args.migrations_dir.exists():
        raise FileNotFoundError(f'Migrations directory does not exist: {args.migrations_dir}')

    migration_files = get_migration_files(args.migrations_dir)

    conn = sqlite3.connect(str(args.db))
    try:
        ensure_migration_table(conn)
        applied_versions = get_applied_versions(conn)

        pending = [path for path in migration_files if migration_version(path) not in applied_versions]

        if not pending:
            print('No pending migrations.')
            return 0

        print('Pending migrations:')
        for path in pending:
            print(f' - {path.name}')

        if args.dry_run:
            print('Dry run complete. No changes applied.')
            return 0

        for path in pending:
            print(f'Applying {path.name} ...')
            apply_migration(conn, path)

        print('Migration run complete.')
        return 0
    finally:
        conn.close()


if __name__ == '__main__':
    raise SystemExit(main())
