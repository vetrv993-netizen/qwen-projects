from datetime import datetime
from typing import List, Optional
from app.database.connection import DatabaseManager

class BranchRepository:
    def __init__(self, db: DatabaseManager): self.db=db
    def get_all(self, active_only=True) -> List[dict]:
        sql='SELECT * FROM branches'
        if active_only: sql+=' WHERE is_active=1'
        sql+=' ORDER BY name_ar'
        return self.db.fetch_all(sql)
    def get_by_id(self, branch_id:int)->Optional[dict]: return self.db.fetch_one('SELECT * FROM branches WHERE id=?',(branch_id,))
    def create(self, **data):
        now=datetime.now().isoformat(); data.setdefault('created_at',now); data.setdefault('updated_at',now)
        return self.db.insert('branches',data)
