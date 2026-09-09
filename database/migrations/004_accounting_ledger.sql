-- Migration 004: Lightweight double-entry accounting and payment allocation
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    name_ar TEXT NOT NULL,
    account_type TEXT NOT NULL CHECK(account_type IN ('asset','liability','equity','revenue','expense')),
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS journal_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_number TEXT NOT NULL UNIQUE,
    entry_date TEXT NOT NULL,
    description TEXT NOT NULL,
    source_type TEXT,
    source_id INTEGER,
    status TEXT NOT NULL DEFAULT 'posted' CHECK(status IN ('posted','reversed')),
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS journal_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    journal_entry_id INTEGER NOT NULL REFERENCES journal_entries(id) ON DELETE CASCADE,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE RESTRICT,
    debit REAL NOT NULL DEFAULT 0,
    credit REAL NOT NULL DEFAULT 0,
    description TEXT,
    created_at TEXT NOT NULL,
    CHECK(debit >= 0 AND credit >= 0 AND NOT (debit > 0 AND credit > 0))
);

CREATE TABLE IF NOT EXISTS payment_allocations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_id INTEGER NOT NULL REFERENCES payments(id) ON DELETE CASCADE,
    invoice_type TEXT NOT NULL CHECK(invoice_type IN ('sale','purchase')),
    invoice_id INTEGER NOT NULL,
    amount REAL NOT NULL CHECK(amount > 0),
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_journal_entries_date ON journal_entries(entry_date);
CREATE INDEX IF NOT EXISTS idx_journal_entries_source ON journal_entries(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_journal_lines_entry ON journal_lines(journal_entry_id);
CREATE INDEX IF NOT EXISTS idx_journal_lines_account ON journal_lines(account_id);
CREATE INDEX IF NOT EXISTS idx_payment_allocations_payment ON payment_allocations(payment_id);
CREATE INDEX IF NOT EXISTS idx_payment_allocations_invoice ON payment_allocations(invoice_type, invoice_id);

INSERT OR IGNORE INTO accounts(code,name,name_ar,account_type,is_active,created_at,updated_at) VALUES
('1000','Cash','الصندوق','asset',1,datetime('now'),datetime('now')),
('1010','Bank','البنك','asset',1,datetime('now'),datetime('now')),
('1100','Accounts Receivable','ذمم العملاء','asset',1,datetime('now'),datetime('now')),
('1200','Inventory','المخزون','asset',1,datetime('now'),datetime('now')),
('2000','Accounts Payable','ذمم الموردين','liability',1,datetime('now'),datetime('now')),
('2100','Sales Tax Payable','ضريبة المبيعات المستحقة','liability',1,datetime('now'),datetime('now')),
('4000','Sales Revenue','إيرادات المبيعات','revenue',1,datetime('now'),datetime('now')),
('5000','Cost of Goods Sold','تكلفة البضاعة المباعة','expense',1,datetime('now'),datetime('now'));

ALTER TABLE payments ADD COLUMN reference_invoice_type TEXT;
ALTER TABLE payments ADD COLUMN reference_invoice_id INTEGER;
