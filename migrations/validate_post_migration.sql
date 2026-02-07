PRAGMA foreign_keys = ON;
PRAGMA integrity_check;

SELECT COUNT(*) AS persons_count FROM persons;
SELECT COUNT(*) AS transactions_count FROM transactions;

SELECT name
FROM sqlite_master
WHERE type = 'table'
  AND name IN ('schema_migrations', 'tax_receipts', 'tax_receipt_items')
ORDER BY name;

SELECT version, applied_at
FROM schema_migrations
ORDER BY version;
