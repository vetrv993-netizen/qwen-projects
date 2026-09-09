"""
Inventory movement repository.
"""
import logging
from typing import Optional, List
from datetime import datetime

from app.database.connection import DatabaseManager


logger = logging.getLogger(__name__)


class InventoryRepository:
    """Repository for inventory movements."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def record_movement(self, **data) -> int:
        data.setdefault('created_at', datetime.now().isoformat())
        return self.db.insert('inventory_movements', data)
    
    def get_by_product(self, product_id: int, limit: int = 50) -> List[dict]:
        return self.db.fetch_all(
            """SELECT * FROM inventory_movements 
               WHERE product_id = ?
               ORDER BY created_at DESC LIMIT ?""",
            (product_id, limit)
        )
    
    def get_all(self, start_date: str = None, end_date: str = None,
                movement_type: str = None, limit: int = 100) -> List[dict]:
        sql = """SELECT im.*, p.name_ar as product_name, p.barcode
                 FROM inventory_movements im
                 JOIN products p ON im.product_id = p.id
                 WHERE 1=1"""
        params = []
        
        if start_date:
            sql += " AND im.created_at >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND im.created_at <= ?"
            params.append(end_date)
        if movement_type:
            sql += " AND im.movement_type = ?"
            params.append(movement_type)
        
        sql += " ORDER BY im.created_at DESC LIMIT ?"
        params.append(limit)
        
        return self.db.fetch_all(sql, tuple(params))
