-- WAFIR v6: assign legacy NULL-branch inventory lots to the active branch.
-- This restores the invariant required by branch-aware FEFO for older databases.
UPDATE inventory_lots
SET branch_id = COALESCE(
    (SELECT CAST(value AS INTEGER) FROM settings WHERE key='current_branch_id' LIMIT 1),
    (SELECT id FROM branches WHERE code='MAIN' LIMIT 1)
),
updated_at = datetime('now')
WHERE branch_id IS NULL;
