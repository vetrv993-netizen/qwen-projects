"""
Supplier repository.
"""
import logging
from typing import Optional, List
from datetime import datetime

from app.database.connection import DatabaseManager


logger = logging.getLogger(__name__)


class SupplierRepository:
    """Repository for Supplier entity."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def create(self, **data) -> int:
        now = datetime.now().isoformat()
        data.setdefault('created_at', now)
        data.setdefault('updated_at', now)
        return self.db.insert('suppliers', data)
    
    def get_by_id(self, supplier_id: int) -> Optional[dict]:
        return self.db.fetch_one("SELECT * FROM suppliers WHERE id = ?", (supplier_id,))
    
    def get_all(self, active_only: bool = True) -> List[dict]:
        sql = "SELECT * FROM suppliers"
        if active_only:
            sql += " WHERE is_active = 1"
        sql += " ORDER BY name_ar"
        return self.db.fetch_all(sql)
    
    def search(self, query: str, limit: int = 50) -> List[dict]:
        return self.db.fetch_all(
            """SELECT * FROM suppliers 
               WHERE (name LIKE ? OR name_ar LIKE ? OR phone LIKE ?)
               AND is_active = 1
               ORDER BY name_ar LIMIT ?""",
            (f'%{query}%', f'%{query}%', f'%{query}%', limit)
        )
    
    def update_balance(self, supplier_id: int, amount_change: float):
        self.db.execute(
            """UPDATE suppliers SET balance = balance + ?,
               updated_at = ? WHERE id = ?""",
            (amount_change, datetime.now().isoformat(), supplier_id)
        )
    
    def update(self, supplier_id: int, **data) -> bool:
        data['updated_at'] = datetime.now().isoformat()
        return self.db.update('suppliers', data, 'id = ?', (supplier_id,)) > 0
    
    def delete(self, supplier_id: int) -> bool:
        return self.db.update('suppliers', {'is_active': 0, 'updated_at': datetime.now().isoformat()}, 'id = ?', (supplier_id,)) > 0
    
    def get_total_payables(self) -> float:
        row = self.db.fetch_one("SELECT COALESCE(SUM(balance), 0) as total FROM suppliers WHERE is_active = 1")
        return row['total'] if row else 0.0
    
    def count(self) -> int:
        row = self.db.fetch_one("SELECT COUNT(*) as count FROM suppliers WHERE is_active = 1")
        return row['count'] if row else 0
