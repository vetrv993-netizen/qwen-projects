"""
Purchase service - business logic for purchase operations.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.database.connection import DatabaseManager
from app.security.permission_enforcer import PermissionEnforcer, PermissionError
from app.security.permissions import Permission
from app.repositories.purchase_repo import PurchaseRepository
from app.repositories.product_repo import ProductRepository
from app.repositories.supplier_repo import SupplierRepository
from app.repositories.inventory_repo import InventoryRepository
from app.repositories.lot_repo import LotRepository
from app.repositories.outbox_repo import OutboxRepository


logger = logging.getLogger(__name__)


class PurchaseService:
    """Business logic for purchase operations."""
    
    def __init__(self, db: DatabaseManager, current_user_id: Optional[int] = None):
        self.db = db
        # Initialize permission enforcer if user is provided
        self.current_user_id = current_user_id
        if current_user_id:
            self.enforcer = PermissionEnforcer(db, current_user_id)
        else:
            self.enforcer = None
        self.purchase_repo = PurchaseRepository(db)
        self.product_repo = ProductRepository(db)
        self.supplier_repo = SupplierRepository(db)
        self.inventory_repo = InventoryRepository(db)
        self.lot_repo = LotRepository(db)
        self.outbox_repo = OutboxRepository(db)
        from app.services.accounting_service import AccountingService
        self.accounting_service = AccountingService(db)
    
    def create_purchase(
        self,
        items: List[Dict[str, Any]],
        supplier_id: Optional[int] = None,
        discount_amount: float = 0,
        tax_rate: float = 0,
        paid_amount: float = 0,
        payment_method: str = 'cash',
        notes: str = '',
        created_by: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create a new purchase.
        
        items: list of {product_id, quantity, unit_cost, discount}
        """
        if not items:
            raise ValueError("لا يمكن إنشاء فاتورة شراء بدون منتجات")
        
        with self.db.transaction():
            subtotal = 0
            purchase_items_data = []
            
            for item in items:
                product = self.product_repo.get_by_id(item['product_id'])
                if not product:
                    raise ValueError(f"المنتج غير موجود: {item['product_id']}")
                
                unit_cost = item.get('unit_cost', product['cost_price'])
                item_discount = item.get('discount', 0)
                item_subtotal = (unit_cost * item['quantity']) - item_discount
                subtotal += item_subtotal
                
                tax_amount = item_subtotal * (tax_rate / 100)
                total_cost = item_subtotal + tax_amount
                
                purchase_items_data.append({
                    'product_id': item['product_id'],
                    'quantity': item['quantity'],
                    'unit_cost': unit_cost,
                    'discount_amount': item_discount,
                    'tax_amount': tax_amount,
                    'total_cost': total_cost,
                })
            
            total_discount = discount_amount
            total_tax = sum(i['tax_amount'] for i in purchase_items_data)
            total_amount = subtotal - total_discount + total_tax
            remaining = total_amount - paid_amount
            
            if remaining <= 0:
                payment_status = 'paid'
            elif paid_amount > 0:
                payment_status = 'partial'
            else:
                payment_status = 'unpaid'
            
            invoice_number = self.purchase_repo.generate_invoice_number()
            
            purchase_id = self.purchase_repo.create_purchase(
                invoice_number=invoice_number,
                supplier_id=supplier_id,
                purchase_date=datetime.now().isoformat(),
                subtotal=subtotal,
                discount_amount=total_discount,
                tax_amount=total_tax,
                total_amount=total_amount,
                paid_amount=paid_amount,
                remaining_amount=remaining,
                payment_status=payment_status,
                status='completed',
                notes=notes,
                created_by=created_by,
            )
            
            # Add purchase items and update inventory
            for item_data in purchase_items_data:
                purchase_item_id = self.purchase_repo.add_purchase_item(purchase_id=purchase_id, **item_data)
                
                # Every purchase creates a traceable stock lot. If the caller supplies
                # a lot number/expiry, retain them; otherwise generate a lot reference.
                lot_number = item_data.get('lot_number') or f"PUR-{purchase_id}-{item_data['product_id']}"
                lot_id = self.lot_repo.create(
                    product_id=item_data['product_id'],
                    branch_id=None,
                    lot_number=lot_number,
                    expiry_date=item_data.get('expiry_date'),
                    unit_cost=item_data['unit_cost'],
                    initial_quantity=item_data['quantity'],
                    current_quantity=item_data['quantity'],
                )
                self.db.insert('purchase_item_lots', {
                    'purchase_item_id': purchase_item_id, 'lot_id': lot_id,
                    'quantity': item_data['quantity'], 'created_at': datetime.now().isoformat()
                })
                
                # Update product stock
                self.product_repo.update_stock(
                    item_data['product_id'],
                    item_data['quantity']
                )
                
                # Update product cost price
                self.product_repo.update(
                    item_data['product_id'],
                    cost_price=item_data['unit_cost']
                )
                
                # Record inventory movement
                self.inventory_repo.record_movement(
                    product_id=item_data['product_id'],
                    movement_type='in',
                    quantity=item_data['quantity'],
                    reference_type='purchase',
                    reference_id=purchase_id,
                    created_by=created_by,
                )
            
            # Update supplier balance if credit purchase
            if supplier_id and remaining > 0:
                self.supplier_repo.update_balance(supplier_id, remaining)
            
            # Record in outbox for sync
            self.outbox_repo.enqueue(
                entity_type='purchase',
                entity_id=str(purchase_id),
                operation_type='create',
                payload={
                    'invoice_number': invoice_number,
                    'total_amount': total_amount,
                    'supplier_id': supplier_id,
                }
            )
            
            self.accounting_service.post_purchase(purchase_id, created_by)
            logger.info(f"Purchase created: {invoice_number}, total: {total_amount}")
            
            return {
                'purchase_id': purchase_id,
                'invoice_number': invoice_number,
                'total_amount': total_amount,
                'paid_amount': paid_amount,
                'remaining': remaining,
                'payment_status': payment_status,
            }
    
    def get_purchase_with_items(self, purchase_id: int) -> Optional[Dict]:
        """Get purchase details with items."""
        purchase = self.purchase_repo.get_by_id(purchase_id)
        if not purchase:
            return None
        
        items = self.purchase_repo.get_items(purchase_id)
        purchase['items'] = items
        return purchase
