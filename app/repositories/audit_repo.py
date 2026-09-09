"""
Audit log repository.

Handles all database operations for audit logs.
"""
import logging
from typing import List, Optional
from datetime import datetime

from app.database.connection import DatabaseManager
from app.domain.models import AuditLog


logger = logging.getLogger(__name__)


class AuditRepository:
    """
    Repository for AuditLog entity.
    
    Provides operations for recording and querying audit events.
    """
    
    def __init__(self, db: DatabaseManager):
        """
        Initialize audit repository.
        
        Args:
            db: Database manager instance
        """
        self.db = db
    
    def log(
        self,
        user_id: int,
        username: str,
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> int:
        """
        Record an audit log entry.
        
        Args:
            user_id: ID of the user performing the action
            username: Username of the user
            action: Action performed (e.g., 'login', 'create_user', 'edit_sale')
            entity_type: Type of entity affected (e.g., 'user', 'sale', 'product')
            entity_id: ID of the affected entity (optional)
            details: Additional details (optional)
            ip_address: IP address (optional, for future cloud sync)
            
        Returns:
            ID of the created audit log entry
        """
        now = datetime.now().isoformat()
        
        return self.db.insert('audit_log', {
            'user_id': user_id,
            'username': username,
            'action': action,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'details': details,
            'ip_address': ip_address,
            'created_at': now,
        })
    
    def get_recent(self, limit: int = 50) -> List[AuditLog]:
        """
        Get recent audit log entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of AuditLog objects
        """
        rows = self.db.fetch_all(
            "SELECT * FROM audit_log ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        
        return [self._row_to_log(row) for row in rows]
    
    def get_by_user(self, user_id: int, limit: int = 50) -> List[AuditLog]:
        """
        Get audit log entries for a specific user.
        
        Args:
            user_id: User ID
            limit: Maximum number of entries
            
        Returns:
            List of AuditLog objects
        """
        rows = self.db.fetch_all(
            "SELECT * FROM audit_log WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit)
        )
        
        return [self._row_to_log(row) for row in rows]
    
    def get_by_action(self, action: str, limit: int = 50) -> List[AuditLog]:
        """
        Get audit log entries for a specific action type.
        
        Args:
            action: Action type to filter by
            limit: Maximum number of entries
            
        Returns:
            List of AuditLog objects
        """
        rows = self.db.fetch_all(
            "SELECT * FROM audit_log WHERE action = ? ORDER BY created_at DESC LIMIT ?",
            (action, limit)
        )
        
        return [self._row_to_log(row) for row in rows]
    
    def get_by_date_range(
        self,
        start_date: str,
        end_date: str,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get audit log entries within a date range.
        
        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            limit: Maximum number of entries
            
        Returns:
            List of AuditLog objects
        """
        rows = self.db.fetch_all(
            """
            SELECT * FROM audit_log 
            WHERE created_at >= ? AND created_at <= ?
            ORDER BY created_at DESC 
            LIMIT ?
            """,
            (start_date, end_date, limit)
        )
        
        return [self._row_to_log(row) for row in rows]
    
    def count(self) -> int:
        """
        Count total audit log entries.
        
        Returns:
            Number of entries
        """
        row = self.db.fetch_one("SELECT COUNT(*) as count FROM audit_log")
        return row['count'] if row else 0
    
    def _row_to_log(self, row: dict) -> AuditLog:
        """Convert a database row to an AuditLog object."""
        return AuditLog(
            id=row['id'],
            user_id=row['user_id'],
            username=row['username'],
            action=row['action'],
            entity_type=row['entity_type'],
            entity_id=row.get('entity_id'),
            details=row.get('details'),
            ip_address=row.get('ip_address'),
            created_at=row['created_at'],
        )
