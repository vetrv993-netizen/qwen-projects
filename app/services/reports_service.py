from datetime import datetime

class ReportsService:
    def __init__(self, db):
        self.db = db

    def customer_statement(self, customer_id: int):
        customer = self.db.fetch_one("SELECT * FROM customers WHERE id=?", (customer_id,))
        if not customer:
            return None
        rows = []
        sales = self.db.fetch_all(
            "SELECT id, invoice_number, sale_date, total_amount, paid_amount, remaining_amount, status "
            "FROM sales WHERE customer_id=? ORDER BY sale_date, id", (customer_id,)
        )
        payments = self.db.fetch_all(
            "SELECT id, amount, payment_date, payment_method, reference_number "
            "FROM payments WHERE payment_type='customer' AND party_id=? ORDER BY payment_date, id", (customer_id,)
        )
        for s in sales:
            rows.append({'date': s['sale_date'], 'type': 'فاتورة بيع', 'reference': s['invoice_number'],
                         'debit': float(s['total_amount'] or 0), 'credit': 0.0, 'status': s['status']})
        for p in payments:
            rows.append({'date': p['payment_date'], 'type': 'تحصيل', 'reference': p.get('reference_number') or f"PAY-{p['id']:06d}",
                         'debit': 0.0, 'credit': float(p['amount'] or 0), 'status': 'posted'})
        rows.sort(key=lambda x: (x['date'], x['reference']))
        balance = 0.0
        for x in rows:
            balance += x['debit'] - x['credit']
            x['balance'] = round(balance, 2)
        return {'party': customer, 'rows': rows, 'balance': round(balance, 2)}

    def supplier_statement(self, supplier_id: int):
        supplier = self.db.fetch_one("SELECT * FROM suppliers WHERE id=?", (supplier_id,))
        if not supplier:
            return None
        rows = []
        purchases = self.db.fetch_all(
            "SELECT id, invoice_number, purchase_date, total_amount, paid_amount, remaining_amount, status "
            "FROM purchases WHERE supplier_id=? ORDER BY purchase_date, id", (supplier_id,)
        )
        payments = self.db.fetch_all(
            "SELECT id, amount, payment_date, payment_method, reference_number "
            "FROM payments WHERE payment_type='supplier' AND party_id=? ORDER BY payment_date, id", (supplier_id,)
        )
        for p in purchases:
            rows.append({'date': p['purchase_date'], 'type': 'فاتورة شراء', 'reference': p['invoice_number'],
                         'debit': 0.0, 'credit': float(p['total_amount'] or 0), 'status': p['status']})
        for p in payments:
            rows.append({'date': p['payment_date'], 'type': 'دفعة للمورد', 'reference': p.get('reference_number') or f"PAY-{p['id']:06d}",
                         'debit': float(p['amount'] or 0), 'credit': 0.0, 'status': 'posted'})
        rows.sort(key=lambda x: (x['date'], x['reference']))
        balance = 0.0
        for x in rows:
            balance += x['credit'] - x['debit']
            x['balance'] = round(balance, 2)
        return {'party': supplier, 'rows': rows, 'balance': round(balance, 2)}

    def expiring_lots(self, days=90, limit=200):
        return self.db.fetch_all(
            """SELECT l.*, p.name_ar AS product_name, p.barcode, b.name_ar AS branch_name
               FROM inventory_lots l
               JOIN products p ON p.id=l.product_id
               LEFT JOIN branches b ON b.id=l.branch_id
               WHERE l.is_active=1 AND l.current_quantity>0
                 AND l.expiry_date IS NOT NULL
                 AND date(l.expiry_date) <= date('now', ? || ' days')
               ORDER BY date(l.expiry_date) ASC, p.name_ar ASC LIMIT ?""",
            (f'+{int(days)}', int(limit))
        )

    def low_stock(self, limit=200):
        return self.db.fetch_all(
            """SELECT id, name_ar, barcode, stock_quantity, min_stock, cost_price, sell_price
               FROM products WHERE is_active=1 AND stock_quantity <= COALESCE(min_stock,0)
               ORDER BY stock_quantity ASC, name_ar ASC LIMIT ?""", (int(limit),)
        )

    def audit_events(self, limit=100):
        return self.db.fetch_all(
            "SELECT * FROM audit_log ORDER BY created_at DESC, id DESC LIMIT ?", (int(limit),)
        )
