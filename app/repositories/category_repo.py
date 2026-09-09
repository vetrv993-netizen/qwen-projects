"""
Category repository.
"""
import logging
from typing import Optional, List
from datetime import datetime

from app.database.connection import DatabaseManager


logger = logging.getLogger(__name__)


class CategoryRepository:
    """Repository for Category entity."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def create(self, **data) -> int:
        now = datetime.now().isoformat()
        data.setdefault('created_at', now)
        data.setdefault('updated_at', now)
        return self.db.insert('categories', data)
    
    def get_by_id(self, category_id: int) -> Optional[dict]:
        return self.db.fetch_one("SELECT * FROM categories WHERE id = ?", (category_id,))
    
    def get_all(self, active_only: bool = True) -> List[dict]:
        sql = "SELECT * FROM categories"
        if active_only:
            sql += " WHERE is_active = 1"
        sql += " ORDER BY sort_order, name_ar"
        return self.db.fetch_all(sql)
    
    def update(self, category_id: int, **data) -> bool:
        data['updated_at'] = datetime.now().isoformat()
        return self.db.update('categories', data, 'id = ?', (category_id,)) > 0
    
    def count(self) -> int:
        row = self.db.fetch_one("SELECT COUNT(*) as count FROM categories WHERE is_active = 1")
        return row['count'] if row else 0
