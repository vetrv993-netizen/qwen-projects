from app.repositories.accounting_repo import AccountingRepository
from app.database.connection import DatabaseManager

class AccountingService:
    def __init__(self, db: DatabaseManager):
        self.db=db
        self.repo=AccountingRepository(db)

    def _line(self, code, debit=0, credit=0, description=None):
        return {'account_id': self.repo.account_id(code), 'debit': debit, 'credit': credit, 'description': description}

    def post_sale(self, sale_id, created_by=None):
        if self.repo.source_entry_exists('sale', sale_id): return
        s=self.db.fetch_one("SELECT * FROM sales WHERE id=?", (sale_id,))
        if not s: return
        lines=[]
        tax=round(max(0.0, float(s['tax_amount'] or 0)), 2)
        total=round(max(0.0, float(s['total_amount'] or 0)), 2)
        paid=round(min(max(0.0, float(s['paid_amount'] or 0)), total), 2)
        rem=round(max(0.0, total-paid), 2)
        if paid: lines.append(self._line('1000', debit=paid, description='تحصيل فوري'))
        if rem: lines.append(self._line('1100', debit=rem, description='ذمم عميل'))
        net_revenue=total-tax
        if net_revenue: lines.append(self._line('4000', credit=net_revenue, description='إيراد مبيعات'))
        if tax: lines.append(self._line('2100', credit=tax, description='ضريبة مبيعات'))
        items=self.db.fetch_all("SELECT si.id, si.quantity, p.cost_price FROM sale_items si JOIN products p ON p.id=si.product_id WHERE si.sale_id=?", (sale_id,))
        cogs=0.0
        for i in items:
            lot_rows=self.db.fetch_all("SELECT quantity, unit_cost FROM sale_item_lots WHERE sale_item_id=?", (i['id'],))
            if lot_rows:
                cogs += sum(float(x['quantity'])*float(x['unit_cost'] or 0) for x in lot_rows)
            else:
                cogs += float(i['quantity'])*float(i['cost_price'] or 0)
        cogs=round(cogs,2)
        if cogs:
            lines.append(self._line('5000', debit=cogs, description='تكلفة البضاعة المباعة'))
            lines.append(self._line('1200', credit=cogs, description='خروج من المخزون'))
        self.repo.create_entry(f"مبيعات {s['invoice_number']}",'sale',sale_id,created_by,lines)

    def post_purchase(self, purchase_id, created_by=None):
        if self.repo.source_entry_exists('purchase', purchase_id): return
        p=self.db.fetch_one("SELECT * FROM purchases WHERE id=?", (purchase_id,))
        if not p: return
        total=round(max(0.0, float(p['total_amount'] or 0)), 2)
        paid=round(min(max(0.0, float(p['paid_amount'] or 0)), total), 2)
        rem=round(max(0.0, total-paid), 2)
        lines=[]
        lines.append(self._line('1200', debit=total, description='إضافة إلى المخزون'))
        if paid: lines.append(self._line('1000', credit=paid, description='دفع للمورّد'))
        if rem: lines.append(self._line('2000', credit=rem, description='ذمم مورّد'))
        self.repo.create_entry(f"مشتريات {p['invoice_number']}",'purchase',purchase_id,created_by,lines)

    def _cash_account(self, payment_method):
        return '1000' if payment_method == 'cash' else '1010'

    def post_customer_payment(self, payment_id, created_by=None):
        if self.repo.source_entry_exists('payment_customer', payment_id): return
        p=self.db.fetch_one("SELECT * FROM payments WHERE id=?", (payment_id,))
        if not p: return
        self.repo.create_entry('تحصيل من عميل','payment_customer',payment_id,created_by,[self._line(self._cash_account(p.get('payment_method')),debit=p['amount']),self._line('1100',credit=p['amount'])])

    def post_supplier_payment(self, payment_id, created_by=None):
        if self.repo.source_entry_exists('payment_supplier', payment_id): return
        p=self.db.fetch_one("SELECT * FROM payments WHERE id=?", (payment_id,))
        if not p: return
        self.repo.create_entry('دفعة لمورّد','payment_supplier',payment_id,created_by,[self._line('2000',debit=p['amount']),self._line(self._cash_account(p.get('payment_method')),credit=p['amount'])])

    def _reverse_entry(self, source_type: str, source_id: int, created_by=None):
        row=self.db.fetch_one("SELECT * FROM journal_entries WHERE source_type=? AND source_id=? AND status='posted' ORDER BY id DESC LIMIT 1",(source_type,source_id))
        if not row: return
        lines=self.db.fetch_all("SELECT * FROM journal_lines WHERE journal_entry_id=? ORDER BY id",(row['id'],))
        reversed_lines=[]
        for line in lines:
            reversed_lines.append(self._line_by_id(line['account_id'],debit=line['credit'],credit=line['debit'],description='قيد عكسي'))
        self.db.update('journal_entries',{'status':'reversed'},'id=?',(row['id'],))
        self.repo.create_entry(f"عكس القيد {row['entry_number']}",'reversal',row['id'],created_by,reversed_lines)

    def _line_by_id(self, account_id, debit=0, credit=0, description=None):
        return {'account_id': account_id, 'debit': debit, 'credit': credit, 'description': description}

    def reverse_sale(self, sale_id, created_by=None):
        self._reverse_entry('sale', sale_id, created_by)

    def reverse_purchase(self, purchase_id, created_by=None):
        self._reverse_entry('purchase', purchase_id, created_by)

    def post_inventory_adjustment(self, product_id, quantity_change, created_by=None, reference_id=None):
        if abs(quantity_change) < 0.00001: return
        product=self.db.fetch_one("SELECT cost_price FROM products WHERE id=?",(product_id,))
        if not product: return
        amount=round(abs(float(quantity_change))*float(product['cost_price'] or 0),2)
        if not amount: return
        if quantity_change>0:
            lines=[self._line('1200',debit=amount,description='زيادة مخزون'),self._line('5000',credit=amount,description='مقابل تسوية')]
        else:
            lines=[self._line('5000',debit=amount,description='نقص مخزون'),self._line('1200',credit=amount,description='مقابل تسوية')]
        self.repo.create_entry('تسوية مخزون','inventory_adjustment',reference_id or product_id,created_by,lines)
