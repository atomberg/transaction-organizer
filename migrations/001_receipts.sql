PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tax_receipts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_number TEXT NOT NULL UNIQUE,
    receipt_type TEXT NOT NULL CHECK (receipt_type IN ('single_transaction', 'annual_person')),
    person_id INTEGER NOT NULL,
    tax_year INTEGER NOT NULL,
    issued_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    issued_by_user_id INTEGER,
    name_snapshot TEXT NOT NULL,
    address_snapshot TEXT,
    org_snapshot TEXT NOT NULL,
    treasurer_snapshot TEXT NOT NULL,
    total_amount REAL NOT NULL CHECK (total_amount >= 0),
    pdf_path TEXT,
    voided_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (person_id) REFERENCES persons(id)
);

CREATE TABLE IF NOT EXISTS tax_receipt_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tax_receipt_id INTEGER NOT NULL,
    transaction_id INTEGER NOT NULL UNIQUE,
    amount REAL NOT NULL CHECK (amount >= 0),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tax_receipt_id) REFERENCES tax_receipts(id) ON DELETE CASCADE,
    FOREIGN KEY (transaction_id) REFERENCES transactions(id)
);

CREATE INDEX IF NOT EXISTS idx_tax_receipts_person_year ON tax_receipts (person_id, tax_year);
CREATE INDEX IF NOT EXISTS idx_tax_receipts_issued_at ON tax_receipts (issued_at);
CREATE INDEX IF NOT EXISTS idx_tax_receipt_items_receipt_id ON tax_receipt_items (tax_receipt_id);

INSERT OR IGNORE INTO schema_migrations (version) VALUES ('001_receipts');
