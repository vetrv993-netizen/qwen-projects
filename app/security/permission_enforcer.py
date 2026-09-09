"""
Permission enforcement for service layer.

This module provides runtime permission checking that is enforced
at the service level, not just UI level. This prevents unauthorized
access even if someone bypasses the UI.
"""
import logging
from typing import Optional, Set, List
from functools import wraps

from app.security.permissions import Permission, Role, has_permission, has_any_permission, has_all_permissions, get_role_permissions
from app.database.connection import DatabaseManager
from app.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)


class PermissionError(Exception):
    """Raised when a user lacks required permission."""
    pass


class PermissionEnforcer:
    """
    Enforces permissions at the service layer.
    
    This class checks permissions for the current user before allowing
    sensitive operations to proceed. It works independently of UI checks.
    """
    
    def __init__(self, db: DatabaseManager, user_id: int):
        """
        Initialize permission enforcer.
        
        Args:
            db: Database manager instance
            user_id: ID of the current user
        """
        self.db = db
        self.user_id = user_id
        self._user_repo = UserRepository(db)
        self._cache = {}  # Simple cache for user data
    
    def _get_user(self) -> Optional[dict]:
        """Get current user data with caching."""
        if self.user_id not in self._cache:
            self._cache[self.user_id] = self._user_repo.get_by_id(self.user_id)
        return self._cache[self.user_id]
    
    def _get_role(self) -> Optional[Role]:
        """Get current user's role enum."""
        user = self._get_user()
        if not user:
            return None
        try:
            return Role(user['role'])
        except (KeyError, ValueError):
            return None
    
    def has_permission(self, permission: Permission) -> bool:
        """
        Check if current user has a specific permission.
        
        Args:
            permission: Permission to check
            
        Returns:
            True if user has permission, False otherwise
        """
        role = self._get_role()
        if not role:
            return False
        
        # Owner and Admin have all permissions
        if role in (Role.OWNER, Role.ADMIN):
            return True
        
        return has_permission(role, permission)
    
    def require_permission(self, permission: Permission):
        """
        Require a specific permission or raise PermissionError.
        
        Args:
            permission: Required permission
            
        Raises:
            PermissionError: If user lacks the permission
        """
        if not self.has_permission(permission):
            user = self._get_user()
            username = user['username'] if user else 'unknown'
            role = self._get_role()
            role_name = role.value if role else 'unknown'
            
            logger.warning(
                f"Permission denied: user '{username}' (role: {role_name}) "
                f"lacks permission '{permission.value}'"
            )
            raise PermissionError(
                f"ليس لديك صلاحية تنفيذ هذه العملية. "
                f"الصلاحية المطلوبة: {permission.value}"
            )
    
    def has_any_permission(self, permissions: List[Permission]) -> bool:
        """
        Check if current user has any of the specified permissions.
        
        Args:
            permissions: List of permissions to check
            
        Returns:
            True if user has at least one permission
        """
        role = self._get_role()
        if not role:
            return False
        
        # Owner and Admin have all permissions
        if role in (Role.OWNER, Role.ADMIN):
            return True
        
        return has_any_permission(role, permissions)
    
    def require_any_permission(self, permissions: List[Permission]):
        """
        Require any of the specified permissions or raise PermissionError.
        
        Args:
            permissions: List of permissions, user needs at least one
            
        Raises:
            PermissionError: If user lacks all permissions
        """
        if not self.has_any_permission(permissions):
            user = self._get_user()
            username = user['username'] if user else 'unknown'
            role = self._get_role()
            role_name = role.value if role else 'unknown'
            
            perm_names = ', '.join(p.value for p in permissions)
            logger.warning(
                f"Permission denied: user '{username}' (role: {role_name}) "
                f"lacks any of: {perm_names}"
            )
            raise PermissionError(
                f"ليس لديك صلاحية تنفيذ هذه العملية. "
                f"الصلاحيات المطلوبة: {perm_names}"
            )
    
    def has_all_permissions(self, permissions: List[Permission]) -> bool:
        """
        Check if current user has all of the specified permissions.
        
        Args:
            permissions: List of permissions to check
            
        Returns:
            True if user has all permissions
        """
        role = self._get_role()
        if not role:
            return False
        
        # Owner and Admin have all permissions
        if role in (Role.OWNER, Role.ADMIN):
            return True
        
        return has_all_permissions(role, permissions)
    
    def require_all_permissions(self, permissions: List[Permission]):
        """
        Require all of the specified permissions or raise PermissionError.
        
        Args:
            permissions: List of permissions, user needs all of them
            
        Raises:
            PermissionError: If user lacks any permission
        """
        if not self.has_all_permissions(permissions):
            user = self._get_user()
            username = user['username'] if user else 'unknown'
            role = self._get_role()
            role_name = role.value if role else 'unknown'
            
            perm_names = ', '.join(p.value for p in permissions)
            logger.warning(
                f"Permission denied: user '{username}' (role: {role_name}) "
                f"lacks all of: {perm_names}"
            )
            raise PermissionError(
                f"ليس لديك صلاحية تنفيذ هذه العملية. "
                f"الصلاحيات المطلوبة: {perm_names}"
            )
    
    def can_access_screen(self, screen_permission: Permission) -> bool:
        """
        Check if user can access a screen/feature.
        
        This is a convenience method for UI checks.
        
        Args:
            screen_permission: Permission required for the screen
            
        Returns:
            True if user can access the screen
        """
        return self.has_permission(screen_permission)
    
    def can_perform_action(self, action_permission: Permission) -> bool:
        """
        Check if user can perform a specific action.
        
        This is a convenience method for UI button/action checks.
        
        Args:
            action_permission: Permission required for the action
            
        Returns:
            True if user can perform the action
        """
        return self.has_permission(action_permission)


def require_permission(permission: Permission):
    """
    Decorator to enforce permission on a service method.
    
    Usage:
        @require_permission(Permission.SALES_CREATE)
        def create_sale(self, ...):
            ...
    
    Args:
        permission: Required permission
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Get enforcer from self (service instance)
            enforcer = getattr(self, 'enforcer', None)
            if enforcer:
                enforcer.require_permission(permission)
            return func(self, *args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(permissions: List[Permission]):
    """
    Decorator to require any of the specified permissions.
    
    Usage:
        @require_any_permission([Permission.SALES_EDIT, Permission.SALES_DELETE])
        def modify_sale(self, ...):
            ...
    
    Args:
        permissions: List of permissions, user needs at least one
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            enforcer = getattr(self, 'enforcer', None)
            if enforcer:
                enforcer.require_any_permission(permissions)
            return func(self, *args, **kwargs)
        return wrapper
    return decorator


def require_all_permissions(permissions: List[Permission]):
    """
    Decorator to require all of the specified permissions.
    
    Usage:
        @require_all_permissions([Permission.SALES_EDIT, Permission.SETTINGS_EDIT])
        def admin_sale_operation(self, ...):
            ...
    
    Args:
        permissions: List of permissions, user needs all of them
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            enforcer = getattr(self, 'enforcer', None)
            if enforcer:
                enforcer.require_all_permissions(permissions)
            return func(self, *args, **kwargs)
        return wrapper
    return decorator
