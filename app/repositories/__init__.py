"""
Repository layer.

Repositories handle all database access for specific entities.
They provide a clean API for the service layer.
"""
from .user_repo import UserRepository
from .audit_repo import AuditRepository
from .outbox_repo import OutboxRepository
from .settings_repo import SettingsRepository
from .product_repo import ProductRepository
from .category_repo import CategoryRepository
from .customer_repo import CustomerRepository
from .supplier_repo import SupplierRepository
from .sale_repo import SaleRepository
from .purchase_repo import PurchaseRepository
from .payment_repo import PaymentRepository
from .inventory_repo import InventoryRepository

__all__ = [
    'UserRepository',
    'AuditRepository',
    'OutboxRepository',
    'SettingsRepository',
    'ProductRepository',
    'CategoryRepository',
    'CustomerRepository',
    'SupplierRepository',
    'SaleRepository',
    'PurchaseRepository',
    'PaymentRepository',
    'InventoryRepository',
]
