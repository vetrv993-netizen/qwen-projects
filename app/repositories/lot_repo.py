from datetime import datetime
from typing import List, Optional
from app.database.connection import DatabaseManager

class LotRepository:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def create(self, **data) -> int:
        now = datetime.now().isoformat()
        data.setdefault('created_at', now)
        data.setdefault('updated_at', now)
        data.setdefault('received_at', now)
        data.setdefault('is_active', 1)
        return self.db.insert('inventory_lots', data)

    def get_by_id(self, lot_id: int) -> Optional[dict]:
        return self.db.fetch_one('SELECT * FROM inventory_lots WHERE id=?', (lot_id,))

    def has_lots(self, product_id: int) -> bool:
        row = self.db.fetch_one('SELECT 1 AS x FROM inventory_lots WHERE product_id=? AND is_active=1 LIMIT 1', (product_id,))
        return row is not None

    def get_available_fefo(self, product_id: int, branch_id: int = None) -> List[dict]:
        sql = """SELECT * FROM inventory_lots
                 WHERE product_id=? AND current_quantity>0 AND is_active=1
                 AND (expiry_date IS NULL OR date(expiry_date) >= date('now'))"""
        params = [product_id]
        if branch_id:
            sql += ' AND branch_id=?'
            params.append(branch_id)
        sql += " ORDER BY CASE WHEN expiry_date IS NULL THEN 1 ELSE 0 END, expiry_date ASC, id ASC"
        return self.db.fetch_all(sql, tuple(params))

    def adjust(self, lot_id: int, quantity_change: float):
        row = self.get_by_id(lot_id)
        if not row:
            raise ValueError('الدفعة غير موجودة')
        new_qty = float(row['current_quantity']) + quantity_change
        if new_qty < -0.00001:
            raise ValueError(f"الكمية غير كافية في الدفعة {row['lot_number']}")
        self.db.update('inventory_lots', {'current_quantity': max(0, new_qty), 'updated_at': datetime.now().isoformat()}, 'id=?', (lot_id,))
