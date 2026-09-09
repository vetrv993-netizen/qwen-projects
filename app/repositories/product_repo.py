"""
Product repository.
"""
import logging
from typing import Optional, List
from datetime import datetime

from app.database.connection import DatabaseManager


logger = logging.getLogger(__name__)


class ProductRepository:
    """Repository for Product entity."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def create(self, **data) -> int:
        now = datetime.now().isoformat()
        data.setdefault('created_at', now)
        data.setdefault('updated_at', now)
        return self.db.insert('products', data)
    
    def get_by_id(self, product_id: int) -> Optional[dict]:
        return self.db.fetch_one("SELECT * FROM products WHERE id = ?", (product_id,))
    
    def get_by_barcode(self, barcode: str) -> Optional[dict]:
        return self.db.fetch_one("SELECT * FROM products WHERE barcode = ?", (barcode,))
    
    def search(self, query: str, limit: int = 50) -> List[dict]:
        return self.db.fetch_all(
            """SELECT * FROM products 
               WHERE (name LIKE ? OR name_ar LIKE ? OR barcode LIKE ?)
               AND is_active = 1
               ORDER BY name_ar LIMIT ?""",
            (f'%{query}%', f'%{query}%', f'%{query}%', limit)
        )
    
    def get_all(self, active_only: bool = True, category_id: int = None) -> List[dict]:
        sql = "SELECT * FROM products"
        params = []
        conditions = []
        
        if active_only:
            conditions.append("is_active = 1")
        if category_id:
            conditions.append("category_id = ?")
            params.append(category_id)
        
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY name_ar"
        
        return self.db.fetch_all(sql, tuple(params))
    
    def get_low_stock(self, limit: int = 50) -> List[dict]:
        return self.db.fetch_all(
            """SELECT * FROM products 
               WHERE is_active = 1 AND stock_quantity <= min_stock AND min_stock > 0
               ORDER BY (stock_quantity / CASE WHEN min_stock = 0 THEN 1 ELSE min_stock END) ASC
               LIMIT ?""",
            (limit,)
        )
    
    def get_expiring(self, days: int = 30, limit: int = 50) -> List[dict]:
        return self.db.fetch_all(
            """SELECT * FROM products 
               WHERE is_active = 1 AND expiry_date IS NOT NULL
               AND expiry_date <= date('now', ? || ' days')
               AND expiry_date >= date('now')
               ORDER BY expiry_date ASC LIMIT ?""",
            (str(days), limit)
        )
    
    def update_stock(self, product_id: int, quantity_change: float):
        self.db.execute(
            """UPDATE products SET stock_quantity = stock_quantity + ?,
               updated_at = ? WHERE id = ?""",
            (quantity_change, datetime.now().isoformat(), product_id)
        )
    
    def update(self, product_id: int, **data) -> bool:
        data['updated_at'] = datetime.now().isoformat()
        return self.db.update('products', data, 'id = ?', (product_id,)) > 0
    
    def delete(self, product_id: int) -> bool:
        return self.db.update('products', {'is_active': 0, 'updated_at': datetime.now().isoformat()}, 'id = ?', (product_id,)) > 0
    
    def count(self) -> int:
        row = self.db.fetch_one("SELECT COUNT(*) as count FROM products WHERE is_active = 1")
        return row['count'] if row else 0
    
    def total_stock_value(self) -> float:
        row = self.db.fetch_one("SELECT COALESCE(SUM(stock_quantity * cost_price), 0) as value FROM products WHERE is_active = 1")
        return row['value'] if row else 0.0
