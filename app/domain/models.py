"""
Domain models / entities.

These are plain Python data classes representing the core business entities.
They are used throughout the application layers.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Set
from enum import Enum

from app.security.permissions import Permission, Role


@dataclass
class User:
    """User entity."""
    id: int
    username: str
    display_name: str
    password_hash: str
    salt: str
    role: str  # Role enum value as string
    is_active: bool = True
    created_at: str = ""
    updated_at: str = ""
    last_login_at: Optional[str] = None
    created_by: Optional[int] = None
    
    def get_role(self) -> Role:
        """Get the Role enum for this user."""
        return Role(self.role)
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if this user has a specific permission."""
        from app.security.permissions import has_permission
        return has_permission(self.get_role(), permission)
    
    def get_permissions(self) -> Set[Permission]:
        """Get all permissions for this user's role."""
        from app.security.permissions import get_role_permissions
        return get_role_permissions(self.get_role())


@dataclass
class Session:
    """User session entity."""
    id: str
    user_id: int
    token: str
    created_at: str
    expires_at: str
    is_active: bool = True
    
    def is_expired(self) -> bool:
        """Check if the session has expired."""
        now = datetime.now()
        expires = datetime.fromisoformat(self.expires_at)
        return now > expires


@dataclass
class AuditLog:
    """Audit log entry."""
    id: int
    user_id: int
    username: str
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: str = ""


@dataclass
class OutboxEntry:
    """
    Outbox entry for future cloud synchronization.
    
    This is the foundation for the outbox pattern.
    Each mutation that should be synced to the cloud
    creates an outbox entry.
    """
    id: int
    operation_id: str
    entity_type: str
    entity_id: str
    operation_type: str  # 'create', 'update', 'delete'
    payload: str  # JSON string
    status: str = 'pending'  # pending, syncing, synced, failed, cancelled
    retry_count: int = 0
    max_retries: int = 5
    last_error: Optional[str] = None
    synced_at: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""


@dataclass
class AppSetting:
    """Application setting."""
    id: int
    key: str
    value: str
    category: str = 'general'
    updated_at: str = ""
