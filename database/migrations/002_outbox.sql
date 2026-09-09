-- Migration 002: Outbox table for future cloud synchronization
-- Implements the outbox pattern for durable sync queue

CREATE TABLE IF NOT EXISTS outbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_id TEXT NOT NULL UNIQUE,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    operation_type TEXT NOT NULL CHECK(operation_type IN ('create', 'update', 'delete')),
    payload TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' 
        CHECK(status IN ('pending', 'syncing', 'synced', 'failed', 'cancelled')),
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 5,
    last_error TEXT,
    synced_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Indexes for outbox performance
CREATE INDEX IF NOT EXISTS idx_outbox_status ON outbox(status);
CREATE INDEX IF NOT EXISTS idx_outbox_operation_id ON outbox(operation_id);
CREATE INDEX IF NOT EXISTS idx_outbox_entity ON outbox(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_outbox_created_at ON outbox(created_at);
CREATE INDEX IF NOT EXISTS idx_outbox_status_retry ON outbox(status, retry_count);
