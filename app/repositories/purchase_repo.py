"""
Purchase repository.
"""
import logging
from typing import Optional, List
from datetime import datetime

from app.database.connection import DatabaseManager


logger = logging.getLogger(__name__)


class PurchaseRepository:
    """Repository for Purchase entity."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def create_purchase(self, **data) -> int:
        now = datetime.now().isoformat()
        data.setdefault('created_at', now)
        data.setdefault('updated_at', now)
        return self.db.insert('purchases', data)
    
    def add_purchase_item(self, **data) -> int:
        data.setdefault('created_at', datetime.now().isoformat())
        return self.db.insert('purchase_items', data)
    
    def get_by_id(self, purchase_id: int) -> Optional[dict]:
        return self.db.fetch_one("SELECT * FROM purchases WHERE id = ?", (purchase_id,))
    
    def get_items(self, purchase_id: int) -> List[dict]:
        return self.db.fetch_all(
            """SELECT pi.*, p.name, p.name_ar, p.barcode, p.unit
               FROM purchase_items pi
               JOIN products p ON pi.product_id = p.id
               WHERE pi.purchase_id = ?
               ORDER BY pi.id""",
            (purchase_id,)
        )
    
    def get_all(self, start_date: str = None, end_date: str = None,
                supplier_id: int = None, limit: int = 100) -> List[dict]:
        sql = """SELECT p.*, s.name as supplier_name, s.name_ar as supplier_name_ar
                 FROM purchases p
                 LEFT JOIN suppliers s ON p.supplier_id = s.id
                 WHERE 1=1"""
        params = []
        
        if start_date:
            sql += " AND p.purchase_date >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND p.purchase_date <= ?"
            params.append(end_date)
        if supplier_id:
            sql += " AND p.supplier_id = ?"
            params.append(supplier_id)
        
        sql += " ORDER BY p.purchase_date DESC, p.id DESC LIMIT ?"
        params.append(limit)
        
        return self.db.fetch_all(sql, tuple(params))
    
    def get_today_total(self) -> float:
        row = self.db.fetch_one(
            """SELECT COALESCE(SUM(total_amount), 0) as total 
               FROM purchases WHERE date(purchase_date) = date('now') AND status = 'completed'"""
        )
        return row['total'] if row else 0.0
    
    def update_payment(self, purchase_id: int, paid_amount: float):
        purchase = self.get_by_id(purchase_id)
        if not purchase:
            return
        
        total = max(0.0, float(purchase['total_amount'] or 0))
        paid_amount = min(max(0.0, float(paid_amount)), total)
        remaining = round(max(0.0, total - paid_amount), 2)
        if remaining <= 0:
            status = 'paid'
        elif paid_amount > 0:
            status = 'partial'
        else:
            status = 'unpaid'
        
        self.db.execute(
            """UPDATE purchases SET paid_amount = ?, remaining_amount = ?,
               payment_status = ?, updated_at = ? WHERE id = ?""",
            (paid_amount, remaining, status, datetime.now().isoformat(), purchase_id)
        )
    
    def update(self, purchase_id: int, **data) -> bool:
        data['updated_at'] = datetime.now().isoformat()
        return self.db.update('purchases', data, 'id = ?', (purchase_id,)) > 0
    
    def get_total_purchases(self, start_date: str = None, end_date: str = None) -> float:
        sql = "SELECT COALESCE(SUM(total_amount), 0) as total FROM purchases WHERE status = 'completed'"
        params = []
        
        if start_date:
            sql += " AND purchase_date >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND purchase_date <= ?"
            params.append(end_date)
        
        row = self.db.fetch_one(sql, tuple(params))
        return row['total'] if row else 0.0
    
    def generate_invoice_number(self) -> str:
        row = self.db.fetch_one("SELECT MAX(id) as max_id FROM purchases")
        next_id = (row['max_id'] or 0) + 1
        return f"PUR-{next_id:06d}"
    
    def count(self) -> int:
        row = self.db.fetch_one("SELECT COUNT(*) as count FROM purchases WHERE status = 'completed'")
        return row['count'] if row else 0
