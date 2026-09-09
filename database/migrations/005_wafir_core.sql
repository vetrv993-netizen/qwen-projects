-- Wafir Core v5: branches, lots/FEFO, document links and operational integrity
CREATE TABLE IF NOT EXISTS branches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    name_ar TEXT NOT NULL,
    address TEXT,
    phone TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS inventory_lots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    branch_id INTEGER REFERENCES branches(id) ON DELETE SET NULL,
    lot_number TEXT NOT NULL,
    expiry_date TEXT,
    unit_cost REAL NOT NULL DEFAULT 0,
    initial_quantity REAL NOT NULL DEFAULT 0,
    current_quantity REAL NOT NULL DEFAULT 0,
    received_at TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(product_id, branch_id, lot_number)
);

CREATE TABLE IF NOT EXISTS sale_item_lots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_item_id INTEGER NOT NULL REFERENCES sale_items(id) ON DELETE CASCADE,
    lot_id INTEGER NOT NULL REFERENCES inventory_lots(id) ON DELETE RESTRICT,
    quantity REAL NOT NULL CHECK(quantity > 0),
    unit_cost REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS purchase_item_lots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    purchase_item_id INTEGER NOT NULL REFERENCES purchase_items(id) ON DELETE CASCADE,
    lot_id INTEGER NOT NULL REFERENCES inventory_lots(id) ON DELETE RESTRICT,
    quantity REAL NOT NULL CHECK(quantity > 0),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS stock_transfers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transfer_number TEXT NOT NULL UNIQUE,
    from_branch_id INTEGER NOT NULL REFERENCES branches(id),
    to_branch_id INTEGER NOT NULL REFERENCES branches(id),
    status TEXT NOT NULL DEFAULT 'completed' CHECK(status IN ('draft','completed','cancelled')),
    transfer_date TEXT NOT NULL,
    notes TEXT,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS stock_transfer_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transfer_id INTEGER NOT NULL REFERENCES stock_transfers(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity REAL NOT NULL CHECK(quantity > 0),
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_lots_product_expiry ON inventory_lots(product_id, expiry_date, id);
CREATE INDEX IF NOT EXISTS idx_lots_branch ON inventory_lots(branch_id);
CREATE INDEX IF NOT EXISTS idx_sale_item_lots_sale_item ON sale_item_lots(sale_item_id);
CREATE INDEX IF NOT EXISTS idx_purchase_item_lots_purchase_item ON purchase_item_lots(purchase_item_id);
CREATE INDEX IF NOT EXISTS idx_transfers_date ON stock_transfers(transfer_date);

-- Default branch for local-first desktop deployments. SaaS can later attach tenant_id.
INSERT OR IGNORE INTO branches(code,name,name_ar,address,phone,is_active,created_at,updated_at)
VALUES('MAIN','Main Branch','الفرع الرئيسي',NULL,NULL,1,datetime('now'),datetime('now'));

INSERT OR IGNORE INTO settings(key,value,category,updated_at)
VALUES('current_branch_id','1','organization',datetime('now'));
