"""
Sale repository.
"""
import logging
from typing import Optional, List
from datetime import datetime

from app.database.connection import DatabaseManager


logger = logging.getLogger(__name__)


class SaleRepository:
    """Repository for Sale entity."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def create_sale(self, **data) -> int:
        now = datetime.now().isoformat()
        data.setdefault('created_at', now)
        data.setdefault('updated_at', now)
        return self.db.insert('sales', data)
    
    def add_sale_item(self, **data) -> int:
        data.setdefault('created_at', datetime.now().isoformat())
        return self.db.insert('sale_items', data)
    
    def get_by_id(self, sale_id: int) -> Optional[dict]:
        return self.db.fetch_one("SELECT * FROM sales WHERE id = ?", (sale_id,))
    
    def get_items(self, sale_id: int) -> List[dict]:
        return self.db.fetch_all(
            """SELECT si.*, p.name, p.name_ar, p.barcode, p.unit
               FROM sale_items si
               JOIN products p ON si.product_id = p.id
               WHERE si.sale_id = ?
               ORDER BY si.id""",
            (sale_id,)
        )
    
    def get_all(self, start_date: str = None, end_date: str = None, 
                customer_id: int = None, status: str = None, limit: int = 100) -> List[dict]:
        sql = """SELECT s.*, c.name as customer_name, c.name_ar as customer_name_ar
                 FROM sales s
                 LEFT JOIN customers c ON s.customer_id = c.id
                 WHERE 1=1"""
        params = []
        
        if start_date:
            sql += " AND s.sale_date >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND s.sale_date <= ?"
            params.append(end_date)
        if customer_id:
            sql += " AND s.customer_id = ?"
            params.append(customer_id)
        if status:
            sql += " AND s.status = ?"
            params.append(status)
        
        sql += " ORDER BY s.sale_date DESC, s.id DESC LIMIT ?"
        params.append(limit)
        
        return self.db.fetch_all(sql, tuple(params))
    
    def get_today_sales(self) -> List[dict]:
        return self.db.fetch_all(
            """SELECT s.*, c.name_ar as customer_name_ar
               FROM sales s
               LEFT JOIN customers c ON s.customer_id = c.id
               WHERE date(s.sale_date) = date('now')
               AND s.status = 'completed'
               ORDER BY s.id DESC"""
        )
    
    def get_today_total(self) -> float:
        row = self.db.fetch_one(
            """SELECT COALESCE(SUM(total_amount), 0) as total 
               FROM sales WHERE date(sale_date) = date('now') AND status = 'completed'"""
        )
        return row['total'] if row else 0.0
    
    def update_payment(self, sale_id: int, paid_amount: float):
        sale = self.get_by_id(sale_id)
        if not sale:
            return
        
        total = max(0.0, float(sale['total_amount'] or 0))
        paid_amount = min(max(0.0, float(paid_amount)), total)
        remaining = round(max(0.0, total - paid_amount), 2)
        if remaining <= 0:
            status = 'paid'
        elif paid_amount > 0:
            status = 'partial'
        else:
            status = 'unpaid'
        
        self.db.execute(
            """UPDATE sales SET paid_amount = ?, remaining_amount = ?,
               payment_status = ?, updated_at = ? WHERE id = ?""",
            (paid_amount, remaining, status, datetime.now().isoformat(), sale_id)
        )
    
    def update(self, sale_id: int, **data) -> bool:
        data['updated_at'] = datetime.now().isoformat()
        return self.db.update('sales', data, 'id = ?', (sale_id,)) > 0
    
    def get_total_revenue(self, start_date: str = None, end_date: str = None) -> float:
        sql = "SELECT COALESCE(SUM(total_amount), 0) as total FROM sales WHERE status = 'completed'"
        params = []
        
        if start_date:
            sql += " AND sale_date >= ?"
            params.append(start_date)
        if end_date:
            sql += " AND sale_date <= ?"
            params.append(end_date)
        
        row = self.db.fetch_one(sql, tuple(params))
        return row['total'] if row else 0.0
    
    def generate_invoice_number(self) -> str:
        row = self.db.fetch_one("SELECT MAX(id) as max_id FROM sales")
        next_id = (row['max_id'] or 0) + 1
        return f"INV-{next_id:06d}"
    
    def count(self) -> int:
        row = self.db.fetch_one("SELECT COUNT(*) as count FROM sales WHERE status = 'completed'")
        return row['count'] if row else 0
