"""
Role-based permission system.

Defines:
- All available permissions
- Role definitions with their permissions
- Permission checking functions
"""
import logging
from enum import Enum
from typing import Set, List


logger = logging.getLogger(__name__)


class Permission(Enum):
    """All available permissions in the system."""
    
    # User management
    USERS_VIEW = "users.view"
    USERS_CREATE = "users.create"
    USERS_EDIT = "users.edit"
    USERS_DELETE = "users.delete"
    
    # Role management
    ROLES_MANAGE = "roles.manage"
    
    # Sales
    SALES_CREATE = "sales.create"
    SALES_VIEW = "sales.view"
    SALES_EDIT = "sales.edit"
    SALES_DELETE = "sales.delete"
    SALES_RETURN = "sales.return"
    
    # Purchases
    PURCHASES_CREATE = "purchases.create"
    PURCHASES_VIEW = "purchases.view"
    PURCHASES_EDIT = "purchases.edit"
    PURCHASES_DELETE = "purchases.delete"
    
    # Inventory
    INVENTORY_VIEW = "inventory.view"
    INVENTORY_CREATE = "inventory.create"
    INVENTORY_EDIT = "inventory.edit"
    INVENTORY_DELETE = "inventory.delete"
    INVENTORY_ADJUST = "inventory.adjust"
    INVENTORY_TRANSFER = "inventory.transfer"
    
    # Customers
    CUSTOMERS_VIEW = "customers.view"
    CUSTOMERS_CREATE = "customers.create"
    CUSTOMERS_EDIT = "customers.edit"
    CUSTOMERS_DELETE = "customers.delete"
    
    # Suppliers
    SUPPLIERS_VIEW = "suppliers.view"
    SUPPLIERS_CREATE = "suppliers.create"
    SUPPLIERS_EDIT = "suppliers.edit"
    SUPPLIERS_DELETE = "suppliers.delete"
    
    # Payments
    PAYMENTS_RECEIVE = "payments.receive"
    PAYMENTS_SEND = "payments.send"
    
    # Reports
    REPORTS_VIEW = "reports.view"
    REPORTS_EXPORT = "reports.export"
    
    # Branches
    BRANCHES_VIEW = "branches.view"
    BRANCHES_CREATE = "branches.create"
    BRANCHES_EDIT = "branches.edit"
    BRANCHES_DELETE = "branches.delete"
    
    # Settings
    SETTINGS_VIEW = "settings.view"
    SETTINGS_EDIT = "settings.edit"
    
    # Backup
    BACKUP_CREATE = "backup.create"
    BACKUP_RESTORE = "backup.restore"
    
    # Audit
    AUDIT_VIEW = "audit.view"


class Role(Enum):
    """System roles."""
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    CASHIER = "cashier"
    ACCOUNTANT = "accountant"
    INVENTORY = "inventory"


# Role permission mappings
ROLE_PERMISSIONS = {
    Role.OWNER: set(Permission),  # Owner has all permissions
    
    Role.ADMIN: {
        Permission.USERS_VIEW, Permission.USERS_CREATE, Permission.USERS_EDIT,
        Permission.ROLES_MANAGE,
        Permission.SALES_CREATE, Permission.SALES_VIEW, Permission.SALES_EDIT,
        Permission.SALES_DELETE, Permission.SALES_RETURN,
        Permission.PURCHASES_CREATE, Permission.PURCHASES_VIEW,
        Permission.PURCHASES_EDIT, Permission.PURCHASES_DELETE,
        Permission.INVENTORY_VIEW, Permission.INVENTORY_CREATE,
        Permission.INVENTORY_EDIT, Permission.INVENTORY_DELETE,
        Permission.INVENTORY_ADJUST, Permission.INVENTORY_TRANSFER,
        Permission.CUSTOMERS_VIEW, Permission.CUSTOMERS_CREATE,
        Permission.CUSTOMERS_EDIT, Permission.CUSTOMERS_DELETE,
        Permission.SUPPLIERS_VIEW, Permission.SUPPLIERS_CREATE,
        Permission.SUPPLIERS_EDIT, Permission.SUPPLIERS_DELETE,
        Permission.PAYMENTS_RECEIVE, Permission.PAYMENTS_SEND,
        Permission.REPORTS_VIEW, Permission.REPORTS_EXPORT,
        Permission.BRANCHES_VIEW, Permission.BRANCHES_CREATE,
        Permission.BRANCHES_EDIT, Permission.BRANCHES_DELETE,
        Permission.SETTINGS_VIEW, Permission.SETTINGS_EDIT,
        Permission.BACKUP_CREATE, Permission.BACKUP_RESTORE,
        Permission.AUDIT_VIEW,
    },
    
    Role.MANAGER: {
        Permission.SALES_CREATE, Permission.SALES_VIEW, Permission.SALES_EDIT,
        Permission.SALES_RETURN,
        Permission.PURCHASES_CREATE, Permission.PURCHASES_VIEW,
        Permission.PURCHASES_EDIT,
        Permission.INVENTORY_VIEW, Permission.INVENTORY_CREATE,
        Permission.INVENTORY_EDIT, Permission.INVENTORY_ADJUST,
        Permission.INVENTORY_TRANSFER,
        Permission.CUSTOMERS_VIEW, Permission.CUSTOMERS_CREATE,
        Permission.CUSTOMERS_EDIT,
        Permission.SUPPLIERS_VIEW, Permission.SUPPLIERS_CREATE,
        Permission.SUPPLIERS_EDIT,
        Permission.PAYMENTS_RECEIVE, Permission.PAYMENTS_SEND,
        Permission.REPORTS_VIEW, Permission.REPORTS_EXPORT,
        Permission.BRANCHES_VIEW,
        Permission.SETTINGS_VIEW,
    },
    
    Role.CASHIER: {
        Permission.SALES_CREATE, Permission.SALES_VIEW,
        Permission.SALES_RETURN,
        Permission.INVENTORY_VIEW,
        Permission.CUSTOMERS_VIEW, Permission.CUSTOMERS_CREATE,
        Permission.PAYMENTS_RECEIVE,
    },
    
    Role.ACCOUNTANT: {
        Permission.SALES_VIEW,
        Permission.PURCHASES_VIEW,
        Permission.INVENTORY_VIEW,
        Permission.CUSTOMERS_VIEW, Permission.CUSTOMERS_EDIT,
        Permission.SUPPLIERS_VIEW, Permission.SUPPLIERS_EDIT,
        Permission.PAYMENTS_RECEIVE, Permission.PAYMENTS_SEND,
        Permission.REPORTS_VIEW, Permission.REPORTS_EXPORT,
        Permission.AUDIT_VIEW,
    },
    
    Role.INVENTORY: {
        Permission.INVENTORY_VIEW, Permission.INVENTORY_CREATE,
        Permission.INVENTORY_EDIT, Permission.INVENTORY_ADJUST,
        Permission.INVENTORY_TRANSFER,
    },
}


def get_role_permissions(role: Role) -> Set[Permission]:
    """
    Get all permissions for a role.
    
    Args:
        role: Role enum value
        
    Returns:
        Set of Permission enum values
    """
    return ROLE_PERMISSIONS.get(role, set())


def has_permission(role: Role, permission: Permission) -> bool:
    """
    Check if a role has a specific permission.
    
    Args:
        role: Role to check
        permission: Permission to check for
        
    Returns:
        True if role has permission, False otherwise
    """
    permissions = get_role_permissions(role)
    return permission in permissions


def has_any_permission(role: Role, permissions: List[Permission]) -> bool:
    """
    Check if a role has any of the specified permissions.
    
    Args:
        role: Role to check
        permissions: List of permissions to check
        
    Returns:
        True if role has at least one permission
    """
    role_permissions = get_role_permissions(role)
    return any(p in role_permissions for p in permissions)


def has_all_permissions(role: Role, permissions: List[Permission]) -> bool:
    """
    Check if a role has all of the specified permissions.
    
    Args:
        role: Role to check
        permissions: List of permissions to check
        
    Returns:
        True if role has all permissions
    """
    role_permissions = get_role_permissions(role)
    return all(p in role_permissions for p in permissions)


def get_role_label(role: Role, language: str = 'ar') -> str:
    """
    Get display label for a role.
    
    Args:
        role: Role enum value
        language: 'ar' for Arabic, 'en' for English
        
    Returns:
        Display label string
    """
    labels = {
        'ar': {
            Role.OWNER: "مالك",
            Role.ADMIN: "مدير النظام",
            Role.MANAGER: "مدير",
            Role.CASHIER: "أمين صندوق",
            Role.ACCOUNTANT: "محاسب",
            Role.INVENTORY: "مسؤول مخزون",
        },
        'en': {
            Role.OWNER: "Owner",
            Role.ADMIN: "Administrator",
            Role.MANAGER: "Manager",
            Role.CASHIER: "Cashier",
            Role.ACCOUNTANT: "Accountant",
            Role.INVENTORY: "Inventory User",
        }
    }
    
    return labels.get(language, labels['ar']).get(role, str(role.value))
