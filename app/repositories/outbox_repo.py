"""
Outbox repository.

Handles all database operations for the outbox (sync queue).
This is the foundation for future cloud synchronization.
"""
import uuid
import json
import logging
from typing import List, Optional
from datetime import datetime

from app.database.connection import DatabaseManager
from app.domain.models import OutboxEntry


logger = logging.getLogger(__name__)


class OutboxRepository:
    """
    Repository for OutboxEntry entity.
    
    The outbox pattern ensures that every local mutation that needs
    to be synced to the cloud is durably recorded before being sent.
    
    This provides:
    - No data loss if the app crashes
    - Retry capability for failed syncs
    - Idempotency via operation_id
    - Ordering guarantees
    """
    
    def __init__(self, db: DatabaseManager):
        """
        Initialize outbox repository.
        
        Args:
            db: Database manager instance
        """
        self.db = db
    
    def enqueue(
        self,
        entity_type: str,
        entity_id: str,
        operation_type: str,
        payload: dict,
    ) -> str:
        """
        Add an entry to the outbox.
        
        Args:
            entity_type: Type of entity (e.g., 'sale', 'customer')
            entity_id: ID of the entity
            operation_type: Type of operation ('create', 'update', 'delete')
            payload: Data to sync (will be JSON-serialized)
            
        Returns:
            Operation ID (UUID) for tracking
        """
        operation_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        self.db.insert('outbox', {
            'operation_id': operation_id,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'operation_type': operation_type,
            'payload': json.dumps(payload, ensure_ascii=False),
            'status': 'pending',
            'retry_count': 0,
            'max_retries': 5,
            'created_at': now,
            'updated_at': now,
        })
        
        logger.debug(f"Outbox entry created: {operation_id} ({operation_type} {entity_type}:{entity_id})")
        return operation_id
    
    def get_pending(self, limit: int = 100) -> List[OutboxEntry]:
        """
        Get pending outbox entries.
        
        Args:
            limit: Maximum number of entries
            
        Returns:
            List of pending OutboxEntry objects
        """
        rows = self.db.fetch_all(
            """
            SELECT * FROM outbox 
            WHERE status = 'pending' AND retry_count < max_retries
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (limit,)
        )
        
        return [self._row_to_entry(row) for row in rows]
    
    def get_by_operation_id(self, operation_id: str) -> Optional[OutboxEntry]:
        """
        Get an outbox entry by operation ID.
        
        Args:
            operation_id: UUID of the operation
            
        Returns:
            OutboxEntry or None
        """
        row = self.db.fetch_one(
            "SELECT * FROM outbox WHERE operation_id = ?",
            (operation_id,)
        )
        
        if row:
            return self._row_to_entry(row)
        return None
    
    def mark_syncing(self, operation_id: str):
        """
        Mark an entry as currently being synced.
        
        Args:
            operation_id: UUID of the operation
        """
        now = datetime.now().isoformat()
        self.db.execute(
            "UPDATE outbox SET status = 'syncing', updated_at = ? WHERE operation_id = ?",
            (now, operation_id)
        )
    
    def mark_synced(self, operation_id: str):
        """
        Mark an entry as successfully synced.
        
        Args:
            operation_id: UUID of the operation
        """
        now = datetime.now().isoformat()
        self.db.execute(
            """
            UPDATE outbox 
            SET status = 'synced', synced_at = ?, updated_at = ?
            WHERE operation_id = ?
            """,
            (now, now, operation_id)
        )
    
    def mark_failed(self, operation_id: str, error: str):
        """
        Mark an entry as failed and increment retry count.
        
        Args:
            operation_id: UUID of the operation
            error: Error message
        """
        now = datetime.now().isoformat()
        self.db.execute(
            """
            UPDATE outbox 
            SET status = 'failed', retry_count = retry_count + 1,
                last_error = ?, updated_at = ?
            WHERE operation_id = ?
            """,
            (error, now, operation_id)
        )
    
    def cancel(self, operation_id: str):
        """
        Cancel an outbox entry (will not be synced).
        
        Args:
            operation_id: UUID of the operation
        """
        now = datetime.now().isoformat()
        self.db.execute(
            "UPDATE outbox SET status = 'cancelled', updated_at = ? WHERE operation_id = ?",
            (now, operation_id)
        )
    
    def cleanup_synced(self, older_than_days: int = 7) -> int:
        """
        Remove old synced entries to keep the table small.
        
        Args:
            older_than_days: Remove entries synced more than this many days ago
            
        Returns:
            Number of entries removed
        """
        cursor = self.db.execute(
            """
            DELETE FROM outbox 
            WHERE status = 'synced' 
            AND synced_at < datetime('now', ? || ' days')
            """,
            (f"-{older_than_days}",)
        )
        return cursor.rowcount
    
    def count_by_status(self, status: str) -> int:
        """
        Count entries with a specific status.
        
        Args:
            status: Status to count
            
        Returns:
            Number of entries
        """
        row = self.db.fetch_one(
            "SELECT COUNT(*) as count FROM outbox WHERE status = ?",
            (status,)
        )
        return row['count'] if row else 0
    
    def get_stats(self) -> dict:
        """
        Get outbox statistics.
        
        Returns:
            Dictionary with counts by status
        """
        rows = self.db.fetch_all(
            "SELECT status, COUNT(*) as count FROM outbox GROUP BY status"
        )
        
        stats = {
            'pending': 0,
            'syncing': 0,
            'synced': 0,
            'failed': 0,
            'cancelled': 0,
            'total': 0,
        }
        
        for row in rows:
            stats[row['status']] = row['count']
            stats['total'] += row['count']
        
        return stats
    
    def _row_to_entry(self, row: dict) -> OutboxEntry:
        """Convert a database row to an OutboxEntry object."""
        return OutboxEntry(
            id=row['id'],
            operation_id=row['operation_id'],
            entity_type=row['entity_type'],
            entity_id=row['entity_id'],
            operation_type=row['operation_type'],
            payload=row['payload'],
            status=row['status'],
            retry_count=row['retry_count'],
            max_retries=row['max_retries'],
            last_error=row.get('last_error'),
            synced_at=row.get('synced_at'),
            created_at=row['created_at'],
            updated_at=row['updated_at'],
        )
