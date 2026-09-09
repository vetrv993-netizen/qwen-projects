"""
User repository.

Handles all database operations for users.
"""
import logging
from typing import Optional, List
from datetime import datetime

from app.database.connection import DatabaseManager
from app.domain.models import User


logger = logging.getLogger(__name__)


class UserRepository:
    """
    Repository for User entity.
    
    Provides CRUD operations and queries for users.
    """
    
    def __init__(self, db: DatabaseManager):
        """
        Initialize user repository.
        
        Args:
            db: Database manager instance
        """
        self.db = db
    
    def create(
        self,
        username: str,
        display_name: str,
        password_hash: str,
        salt: str,
        role: str,
        created_by: Optional[int] = None,
    ) -> int:
        """
        Create a new user.
        
        Args:
            username: Unique username
            display_name: Display name
            password_hash: Hashed password
            salt: Password salt
            role: Role name
            created_by: ID of user who created this user
            
        Returns:
            ID of the created user
        """
        now = datetime.now().isoformat()
        
        return self.db.insert('users', {
            'username': username,
            'display_name': display_name,
            'password_hash': password_hash,
            'salt': salt,
            'role': role,
            'is_active': 1,
            'created_at': now,
            'updated_at': now,
            'created_by': created_by,
        })
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Get a user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User object or None
        """
        row = self.db.fetch_one(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        )
        
        if row:
            return self._row_to_user(row)
        return None
    
    def get_by_username(self, username: str) -> Optional[User]:
        """
        Get a user by username.
        
        Args:
            username: Username
            
        Returns:
            User object or None
        """
        row = self.db.fetch_one(
            "SELECT * FROM users WHERE username = ? AND is_active = 1",
            (username,)
        )
        
        if row:
            return self._row_to_user(row)
        return None
    
    def get_all(self, active_only: bool = True) -> List[User]:
        """
        Get all users.
        
        Args:
            active_only: If True, only return active users
            
        Returns:
            List of User objects
        """
        if active_only:
            rows = self.db.fetch_all(
                "SELECT * FROM users WHERE is_active = 1 ORDER BY display_name"
            )
        else:
            rows = self.db.fetch_all(
                "SELECT * FROM users ORDER BY display_name"
            )
        
        return [self._row_to_user(row) for row in rows]
    
    def update(self, user_id: int, **kwargs) -> bool:
        """
        Update a user.
        
        Args:
            user_id: User ID
            **kwargs: Fields to update
            
        Returns:
            True if updated, False if not found
        """
        kwargs['updated_at'] = datetime.now().isoformat()
        
        rows_affected = self.db.update(
            'users',
            kwargs,
            'id = ?',
            (user_id,)
        )
        
        return rows_affected > 0
    
    def update_last_login(self, user_id: int):
        """
        Update the last login timestamp for a user.
        
        Args:
            user_id: User ID
        """
        now = datetime.now().isoformat()
        self.db.execute(
            "UPDATE users SET last_login_at = ?, updated_at = ? WHERE id = ?",
            (now, now, user_id)
        )
    
    def deactivate(self, user_id: int) -> bool:
        """
        Deactivate a user (soft delete).
        
        Args:
            user_id: User ID
            
        Returns:
            True if deactivated
        """
        return self.update(user_id, is_active=0)
    
    def activate(self, user_id: int) -> bool:
        """
        Activate a user.
        
        Args:
            user_id: User ID
            
        Returns:
            True if activated
        """
        return self.update(user_id, is_active=1)
    
    def delete(self, user_id: int) -> bool:
        """
        Permanently delete a user.
        
        WARNING: This cannot be undone. Use deactivate() for soft delete.
        
        Args:
            user_id: User ID
            
        Returns:
            True if deleted
        """
        rows_affected = self.db.delete('users', 'id = ?', (user_id,))
        return rows_affected > 0
    
    def exists(self, username: str) -> bool:
        """
        Check if a username already exists.
        
        Args:
            username: Username to check
            
        Returns:
            True if exists
        """
        row = self.db.fetch_one(
            "SELECT id FROM users WHERE username = ?",
            (username,)
        )
        return row is not None
    
    def count(self, active_only: bool = True) -> int:
        """
        Count users.
        
        Args:
            active_only: If True, only count active users
            
        Returns:
            Number of users
        """
        if active_only:
            row = self.db.fetch_one(
                "SELECT COUNT(*) as count FROM users WHERE is_active = 1"
            )
        else:
            row = self.db.fetch_one(
                "SELECT COUNT(*) as count FROM users"
            )
        
        return row['count'] if row else 0
    
    def _row_to_user(self, row: dict) -> User:
        """Convert a database row to a User object."""
        return User(
            id=row['id'],
            username=row['username'],
            display_name=row['display_name'],
            password_hash=row['password_hash'],
            salt=row['salt'],
            role=row['role'],
            is_active=bool(row['is_active']),
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            last_login_at=row.get('last_login_at'),
            created_by=row.get('created_by'),
        )
