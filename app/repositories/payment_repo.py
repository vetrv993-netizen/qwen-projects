"""
Payment repository.
"""
import logging
from typing import Optional, List
from datetime import datetime

from app.database.connection import DatabaseManager


logger = logging.getLogger(__name__)


class PaymentRepository:
    """Repository for Payment entity."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def create(self, **data) -> int:
        data.setdefault('created_at', datetime.now().isoformat())
        return self.db.insert('payments', data)
    
    def get_by_id(self, payment_id: int) -> Optional[dict]:
        return self.db.fetch_one("SELECT * FROM payments WHERE id = ?", (payment_id,))
    
    def get_customer_payments(self, customer_id: int, limit: int = 50) -> List[dict]:
        return self.db.fetch_all(
            """SELECT * FROM payments 
               WHERE payment_type = 'customer' AND party_id = ?
               ORDER BY payment_date DESC LIMIT ?""",
            (customer_id, limit)
        )
    
    def get_supplier_payments(self, supplier_id: int, limit: int = 50) -> List[dict]:
        return self.db.fetch_all(
            """SELECT * FROM payments 
               WHERE payment_type = 'supplier' AND party_id = ?
               ORDER BY payment_date DESC LIMIT ?""",
            (supplier_id, limit)
        )
    
    def get_today_total(self, payment_type: str = None) -> float:
        sql = """SELECT COALESCE(SUM(amount), 0) as total 
                 FROM payments WHERE date(payment_date) = date('now')"""
        params = []
        
        if payment_type:
            sql += " AND payment_type = ?"
            params.append(payment_type)
        
        row = self.db.fetch_one(sql, tuple(params))
        return row['total'] if row else 0.0
    
    def get_all(self, start_date: str = None, end_date: str = None,
                payment_type: str = None, limit: int = 100) -> List[dict]:
        sql = "SELECT * FROM payments WHERE 1=1"
        params = []
        
        if start_date:
            sql += " AND payment_date >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND payment_date <= ?"
            params.append(end_date)
        if payment_type:
            sql += " AND payment_type = ?"
            params.append(payment_type)
        
        sql += " ORDER BY payment_date DESC, id DESC LIMIT ?"
        params.append(limit)
        
        return self.db.fetch_all(sql, tuple(params))
