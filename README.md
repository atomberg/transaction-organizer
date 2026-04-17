# transaction-organizer

Transaction and donor-family organizer built with Flask + SQLite.

## Current workflow

1. Donor-first UI.
2. Each donor is stored in `persons` and belongs to a family (`families` + `family_members`).
3. A newly created donor automatically gets a family of one.
4. Each family can have at most 2 active members.
5. Family address and notes are shared across members.

## App entrypoints

1. Development server:
```bash
python server_debug.py
```

2. Production-style server (waitress):
```bash
python server.py
```

## Core routes

### Donors / family

1. `GET /` -> redirects to `/donors`
2. `GET /donors`
3. `GET /donors/add`
4. `POST /donors/add`
5. `GET /donors/<donor_id>`
6. `GET /donors/<donor_id>/edit`
7. `POST /donors/<donor_id>/edit`
8. `POST /donors/<donor_id>/remove`
9. `POST /donors/<donor_id>/members/<person_id>/remove`
10. `POST /donors/<donor_id>/family` (shared family address + notes)
11. `GET /donors/<donor_id>/spouse/add`
12. `POST /donors/<donor_id>/spouse/add`
13. `GET /donors/<donor_id>/receipts`
14. `GET /donors/<donor_id>/receipt/<year>`
15. `GET /donors/<donor_id>/receipt/<year>/pdf`
16. `GET /donors/receipts/<receipt_id>`
17. `GET /donors/receipts/<receipt_id>/pdf`

### Transactions

1. `GET /transactions`
2. `POST /transactions`
3. `GET /transactions/<transaction_id>`
4. `GET /transactions/<transaction_id>/delete`
5. `GET /transactions/<transaction_id>/receipt`
6. `GET /transactions/<transaction_id>/receipt/pdf`
7. `GET /transactions/data`
8. `GET /transactions/export`

Notes:
1. `/transactions` defaults to last 12 months when no filters are provided, by redirecting to:
   `/transactions/?begin=<today-365days>&end=`
2. Transaction create/update requires `donor_id`.

### Reports

1. `GET /reports`
2. `POST /reports` (parse uploaded spreadsheets)
3. `POST /reports/export` (export parsed report)

## Data model summary

1. `persons`: donor identity rows.
2. `families`: shared household entity.
3. `family_members`: links person <-> family, with max 2 active members per family.
4. `transactions`: donations linked by `person_id`.
5. `tax_receipts` and `tax_receipt_items`: issued receipt records and included transactions.

Receipt recipient linkage:
1. `tax_receipts.donor_id` is used as donor-recipient pointer.
2. `tax_receipts.person_id` remains present for compatibility in current schema.

## Legacy DB import

Script:
```bash
python scripts/import_legacy_db.py --source-db <legacy.db> --target-db <new.db> --force
```

Current importer behavior:
1. Creates a fresh target DB with the current schema.
2. Imports persons preserving IDs.
3. Creates one family per imported person with `family.id == person.id`.
4. Creates one family_members row linking that person to the same family ID.
5. Copies `persons.address` and `persons.notes` to family shared fields.
6. Preserves `created_at`, `updated_at`, `deleted_at`.
7. Imports transactions.
8. Appends legacy `accepted_by` to the end of new transaction `memo` (space-separated).

## Testing

Run non-report suite:
```bash
PYTHONPATH=. python -m pytest -q tests --ignore=tests/test_parse_reports.py --ignore=tests/test_reports.py
```
