from datetime import datetime
from app.repositories.lot_repo import LotRepository
from app.repositories.branch_repo import BranchRepository
from app.repositories.audit_repo import AuditRepository

class WafirCoreService:
    """Cross-module operational helpers for Wafir's local-first core."""
    def __init__(self, db):
        self.db = db
        self.lots = LotRepository(db)
        self.branches = BranchRepository(db)
        self.audit = AuditRepository(db)

    def current_branch_id(self):
        row = self.db.fetch_one("SELECT value FROM settings WHERE key=?", ("current_branch_id",))
        return int(row["value"]) if row and str(row["value"]).isdigit() else None

    def record_event(self, user, action, entity_type, entity_id=None, details=None):
        return self.audit.log(user_id=user.id, username=user.username, action=action, entity_type=entity_type,
                              entity_id=str(entity_id) if entity_id is not None else None,
                              details=details)
