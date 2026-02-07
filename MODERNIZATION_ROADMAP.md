# Transaction Organizer Modernization Roadmap

## Goals and Priorities

This roadmap is ordered by your stated priorities:

1. Tax receipt system improvements first
2. Family/household donor support second
3. Users and audit logging third

Key constraints:

- Existing production data is large and important (`~4,500` transactions, `~687` people).
- Production runs on a Windows laptop with limited access windows.
- Migration must be low-risk, easy to execute on-site, and easy to roll back.

---

## Phase 1: Tax Receipt System (First Priority)

### 1. Receipt Data Model (new tables)

Add normalized receipt tables so issued receipts are real records, not just a manual boolean:

- `tax_receipts`
  - `id` (PK)
  - `receipt_number` (unique)
  - `receipt_type` (`single_transaction` or `annual`)
  - `tax_year` (int)
  - `donor_entity_id` (nullable for now; person-based initially)
  - `issued_at` (datetime)
  - `issued_by_user_id` (nullable; populated in Phase 3)
  - `name_snapshot`, `address_snapshot`, `org_snapshot`, `treasurer_snapshot`
  - `total_amount`
  - `pdf_path` or `pdf_blob_id` (implementation choice)
  - `voided_at` (nullable, for future reissue flow)

- `tax_receipt_items`
  - `id` (PK)
  - `tax_receipt_id` (FK -> `tax_receipts`)
  - `transaction_id` (FK -> `transactions`)
  - unique constraint on (`tax_receipt_id`, `transaction_id`)

### 2. Automation of "Tax Receipt Issued"

- Keep existing `transactions.receipt` temporarily.
- On receipt issuance:
  - create `tax_receipts` row
  - create `tax_receipt_items` rows for linked transactions
  - set `transactions.receipt = 1` for linked transactions (for compatibility)
- Stop manual toggling in UI once issuance flow is live.

### 3. Tax Year + Historical Retrieval UX

- Add tax-year selector in receipts UI.
- Add donor receipt history page:
  - all receipts for a donor
  - filter by year and receipt type
  - view/download existing PDFs
- Add annual issuance flow:
  - choose year
  - generate one receipt covering all eligible transactions

### 4. PDF Download Support

- Keep HTML preview.
- Add explicit "Download PDF" for:
  - single transaction receipt
  - annual donor receipt
- Persist receipt record so historical PDFs are re-downloadable.

---

## Phase 2: Family/Household Donor Support (Second Priority)

### 1. Donor Entity Model

- Add `donor_entities` (`person` or `family`)
- Add `donor_entity_members`
  - links people to a family entity
- Transactions can remain person-owned; receipts can be issued to a family entity.

### 2. Receipt Aggregation Behavior

- Single receipt: issue to selected person/family.
- Annual receipt: aggregate eligible transactions for all family members.

### 3. UI

- Family management page:
  - create family
  - assign/unassign people
  - define display name and mailing address for receipt
- Receipt screens:
  - recipient selector (person/family)
  - clear totals preview before issue

---

## Phase 3: Users + Audit Log (Third Priority)

### 1. Users

- Add internal users with role-based access:
  - `admin`, `staff`, `viewer`
- Start with local username/password auth.

### 2. Audit Log

- Add `audit_log` table:
  - `id`, `actor_user_id`, `action`, `target_type`, `target_id`
  - `created_at`
  - `before_json`, `after_json`
  - optional `request_id`
- Log at minimum:
  - person create/update/delete
  - transaction create/update/delete
  - receipt issue/reissue/download
  - login events

---

## Membership Donations (Cross-Cutting Enhancement)

Add membership support without breaking existing donations:

- Extend transactions with:
  - `transaction_kind` (`donation` or `membership`)
  - `membership_year` (nullable)
- Add membership-focused UI:
  - year filter
  - paid/not-paid tracking
  - AGM summary/export

---

## Migration Strategy (Safety First)

## Non-Negotiable Safety Rules

1. Never migrate the original DB file directly.
2. Always migrate a copied DB file.
3. Validate row counts and DB integrity after migration.
4. Only switch app to migrated DB after smoke tests pass.
5. Keep original DB untouched for immediate rollback.

## Proposed Migration Tooling

Use SQL migration files plus one migration metadata table:

- `migrations/001_receipts.sql`
- `migrations/002_family_entities.sql`
- `migrations/003_users_audit.sql`

Each migration should:

- use `BEGIN IMMEDIATE; ... COMMIT;`
- be idempotent where possible (`CREATE TABLE IF NOT EXISTS`)
- insert its version into:
  - `schema_migrations(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)`

---

## On-Site Windows Migration Runbook (Bulletproof Version)

These steps assume SQLite DB file deployment.

## A. Pre-visit prep (done locally before going on-site)

1. Prepare release package:
   - app code
   - migration SQL files
   - validation SQL script
2. Test migration against a recent copy of production-like DB locally.
3. Print/save this runbook with exact commands.

## B. On-site execution

1. Stop the running app.
2. Create timestamped backup folder.
3. Copy production DB into backup and working copy.
4. Run migration SQL on working copy only.
5. Run validation SQL checks.
6. Start new app against migrated working copy.
7. Perform smoke tests in browser.
8. If good: point app to migrated DB.
9. Keep original DB backup untouched.

## C. PowerShell command template

Adjust paths as needed:

```powershell
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$root = "C:\transaction-organizer"
$db = Join-Path $root "transactions.db"
$backupDir = Join-Path $root ("backups\migration_" + $ts)
New-Item -ItemType Directory -Path $backupDir | Out-Null

Copy-Item $db (Join-Path $backupDir "transactions_original.db")
Copy-Item $db (Join-Path $backupDir "transactions_working.db")

# Run migrations on working copy only
sqlite3 (Join-Path $backupDir "transactions_working.db") ".read migrations\001_receipts.sql"
sqlite3 (Join-Path $backupDir "transactions_working.db") ".read migrations\002_family_entities.sql"
sqlite3 (Join-Path $backupDir "transactions_working.db") ".read migrations\003_users_audit.sql"

# Run validation checks
sqlite3 (Join-Path $backupDir "transactions_working.db") ".read migrations\validate_post_migration.sql"
```

## D. Validation SQL checklist (must pass before cutover)

At minimum verify:

- DB integrity:
  - `PRAGMA integrity_check;` -> `ok`
- Row counts unchanged for existing tables:
  - persons count should remain `687` (or current real count)
  - transactions count should remain `4500` (or current real count)
- New tables exist.
- Existing app read flows still work.

Example validation SQL:

```sql
PRAGMA integrity_check;
SELECT COUNT(*) AS persons_count FROM persons;
SELECT COUNT(*) AS transactions_count FROM transactions;
SELECT name FROM sqlite_master WHERE type='table'
AND name IN ('tax_receipts', 'tax_receipt_items', 'donor_entities', 'audit_log');
```

## E. Cutover

After successful smoke test:

1. Keep original as-is.
2. Replace app DB reference/path to working migrated DB.
3. Restart app.

## F. Rollback (fast)

If anything fails:

1. Stop app.
2. Restore original DB from backup.
3. Restart old app version.

No destructive operations needed.

---

## Implementation Slice Plan (Recommended PR Order)

1. Receipt schema + migrations + issuance service (no UI change yet).
2. Receipt UI (year selector, issue, history, download PDF).
3. Remove manual receipt toggle and make status derived/automated.
4. Family entities schema + management UI.
5. Family-aware receipt issuance.
6. Membership transaction kind/year + AGM screen.
7. Users/auth.
8. Audit logging.

---

## Definition of Done (per phase)

- Migrations run cleanly on a copied production DB.
- Row counts for existing core tables unchanged post-migration.
- `PRAGMA integrity_check` returns `ok`.
- Existing tests pass; new feature tests added.
- Manual smoke test checklist completed on Windows environment.
