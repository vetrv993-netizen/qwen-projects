from datetime import datetime
from typing import List, Optional
from app.database.connection import DatabaseManager

class AccountingRepository:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def account_id(self, code: str) -> int:
        row = self.db.fetch_one("SELECT id FROM accounts WHERE code = ?", (code,))
        if not row:
            raise ValueError(f"الحساب غير موجود: {code}")
        return row['id']

    def create_entry(self, description: str, source_type: str, source_id: int, created_by: Optional[int], lines: List[dict], entry_date: Optional[str] = None) -> int:
        if not lines:
            raise ValueError("القيد المحاسبي فارغ")
        debit = round(sum(float(x.get('debit', 0)) for x in lines), 2)
        credit = round(sum(float(x.get('credit', 0)) for x in lines), 2)
        if abs(debit - credit) > 0.01:
            raise ValueError(f"القيد غير متوازن: مدين {debit} دائن {credit}")
        now = datetime.now().isoformat()
        row = self.db.fetch_one("SELECT COALESCE(MAX(id),0)+1 next_id FROM journal_entries")
        entry_no = f"JE-{row['next_id']:08d}"
        entry_id = self.db.insert('journal_entries', {
            'entry_number': entry_no, 'entry_date': entry_date or now, 'description': description,
            'source_type': source_type, 'source_id': source_id, 'status': 'posted',
            'created_by': created_by, 'created_at': now,
        })
        for line in lines:
            if not line.get('debit') and not line.get('credit'):
                continue
            self.db.insert('journal_lines', {
                'journal_entry_id': entry_id, 'account_id': line['account_id'],
                'debit': float(line.get('debit', 0)), 'credit': float(line.get('credit', 0)),
                'description': line.get('description'), 'created_at': now,
            })
        return entry_id

    def source_entry_exists(self, source_type: str, source_id: int) -> bool:
        return self.db.fetch_one("SELECT id FROM journal_entries WHERE source_type=? AND source_id=? AND status='posted' LIMIT 1", (source_type, source_id)) is not None

    def get_trial_balance(self):
        return self.db.fetch_all("""
            SELECT a.code,a.name_ar,a.account_type,
                   COALESCE(SUM(jl.debit),0) debit,
                   COALESCE(SUM(jl.credit),0) credit,
                   COALESCE(SUM(jl.debit-jl.credit),0) balance
            FROM accounts a
            LEFT JOIN journal_lines jl ON jl.account_id=a.id
            WHERE a.is_active=1
            GROUP BY a.id
            ORDER BY a.code
        """)

    def get_entries(self, limit=200):
        return self.db.fetch_all("SELECT * FROM journal_entries ORDER BY entry_date DESC,id DESC LIMIT ?", (limit,))
