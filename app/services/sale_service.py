"""
Sale service - business logic for sales operations.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, date

from app.database.connection import DatabaseManager
from app.repositories.sale_repo import SaleRepository
from app.repositories.product_repo import ProductRepository
from app.repositories.customer_repo import CustomerRepository
from app.repositories.inventory_repo import InventoryRepository
from app.repositories.outbox_repo import OutboxRepository
from app.repositories.lot_repo import LotRepository


logger = logging.getLogger(__name__)


class SaleService:
    """Business logic for sales operations."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.sale_repo = SaleRepository(db)
        self.product_repo = ProductRepository(db)
        self.customer_repo = CustomerRepository(db)
        self.inventory_repo = InventoryRepository(db)
        self.outbox_repo = OutboxRepository(db)
        self.lot_repo = LotRepository(db)
        from app.services.accounting_service import AccountingService
        self.accounting_service = AccountingService(db)
    
    def create_sale(
        self,
        items: List[Dict[str, Any]],
        customer_id: Optional[int] = None,
        discount_amount: float = 0,
        tax_rate: float = 0,
        paid_amount: float = 0,
        payment_method: str = 'cash',
        notes: str = '',
        created_by: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create a new sale.
        
        items: list of {product_id, quantity, unit_price, discount}
        """
        if not items:
            raise ValueError("لا يمكن إنشاء فاتورة بدون منتجات")
        if discount_amount < 0 or tax_rate < 0 or paid_amount < 0:
            raise ValueError("الخصم والضريبة والمدفوع لا يمكن أن تكون سالبة")
        
        with self.db.transaction():
            # Calculate totals
            subtotal = 0
            sale_items_data = []
            
            for item in items:
                product = self.product_repo.get_by_id(item['product_id'])
                if not product:
                    raise ValueError(f"المنتج غير موجود: {item['product_id']}")
                
                quantity = float(item.get('quantity', 0))
                if quantity <= 0:
                    raise ValueError("كمية البيع يجب أن تكون أكبر من صفر")
                if product['stock_quantity'] < quantity:
                    raise ValueError(f"الكمية غير متوفرة للمنتج: {product['name_ar']}")
                if product.get('expiry_date'):
                    try:
                        branch_row = self.db.fetch_one("SELECT value FROM settings WHERE key='current_branch_id' LIMIT 1")
                        try:
                            branch_id = int(branch_row['value']) if branch_row and branch_row.get('value') else None
                        except (TypeError, ValueError):
                            branch_id = None
                        if date.fromisoformat(str(product['expiry_date'])) < date.today() and not self.lot_repo.has_lots(product['id'], branch_id=branch_id):
                            raise ValueError(f"لا يمكن بيع المنتج منتهي الصلاحية: {product['name_ar']}")
                    except ValueError as exc:
                        if 'لا يمكن بيع المنتج' in str(exc):
                            raise
                
                unit_price = float(item.get('unit_price', product['selling_price']))
                item_discount = float(item.get('discount', 0))
                if unit_price < 0 or item_discount < 0:
                    raise ValueError("سعر البيع والخصم لا يمكن أن يكونا سالبين")
                item_subtotal = (unit_price * quantity) - item_discount
                if item_subtotal < 0:
                    raise ValueError("خصم الصنف يتجاوز قيمة الصنف")
                subtotal += item_subtotal
                
                tax_amount = item_subtotal * (tax_rate / 100)
                total_price = item_subtotal + tax_amount
                
                sale_items_data.append({
                    'product_id': item['product_id'],
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'discount_amount': item_discount,
                    'tax_amount': tax_amount,
                    'total_price': total_price,
                })
            
            total_discount = discount_amount
            total_tax = sum(i['tax_amount'] for i in sale_items_data)
            total_amount = subtotal - total_discount + total_tax
            remaining = total_amount - paid_amount
            
            if remaining <= 0:
                payment_status = 'paid'
            elif paid_amount > 0:
                payment_status = 'partial'
            else:
                payment_status = 'unpaid'
            
            invoice_number = self.sale_repo.generate_invoice_number()
            
            sale_id = self.sale_repo.create_sale(
                invoice_number=invoice_number,
                customer_id=customer_id,
                sale_date=datetime.now().isoformat(),
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
            
            # Add sale items and update inventory
            for item_data in sale_items_data:
                sale_item_id = self.sale_repo.add_sale_item(sale_id=sale_id, **item_data)
                
                # Update product stock and allocate FEFO lots when available.
                self.product_repo.update_stock(item_data['product_id'], -item_data['quantity'])
                remaining_qty = float(item_data['quantity'])
                branch_row = self.db.fetch_one("SELECT value FROM settings WHERE key='current_branch_id' LIMIT 1")
                try:
                    branch_id = int(branch_row['value']) if branch_row and branch_row.get('value') else None
                except (TypeError, ValueError):
                    branch_id = None
                lots = self.lot_repo.get_available_fefo(item_data['product_id'], branch_id=branch_id)
                if self.lot_repo.has_lots(item_data['product_id'], branch_id=branch_id) and not lots:
                    raise ValueError(f"لا يمكن بيع منتج منتهي الصلاحية أو لا توجد دفعات صالحة: {product['name_ar']}")
                for lot in lots:
                    if remaining_qty <= 0.00001:
                        break
                    take = min(remaining_qty, float(lot['current_quantity']))
                    self.lot_repo.adjust(lot['id'], -take)
                    self.db.insert('sale_item_lots', {
                        'sale_item_id': sale_item_id,
                        'lot_id': lot['id'],
                        'quantity': take,
                        'unit_cost': float(lot.get('unit_cost') or 0),
                        'created_at': datetime.now().isoformat(),
                    })
                    remaining_qty -= take
                if lots and remaining_qty > 0.00001:
                    raise ValueError(f"الكمية المتاحة في الدفعات غير كافية للمنتج: {product['name_ar']}")
                
                # Record inventory movement
                self.inventory_repo.record_movement(
                    product_id=item_data['product_id'],
                    movement_type='out',
                    quantity=item_data['quantity'],
                    reference_type='sale',
                    reference_id=sale_id,
                    created_by=created_by,
                )
            
            # Update customer balance if credit sale
            if customer_id and remaining > 0:
                self.customer_repo.update_balance(customer_id, remaining)
            
            # Record in outbox for sync
            self.outbox_repo.enqueue(
                entity_type='sale',
                entity_id=str(sale_id),
                operation_type='create',
                payload={
                    'invoice_number': invoice_number,
                    'total_amount': total_amount,
                    'customer_id': customer_id,
                }
            )
            
            self.accounting_service.post_sale(sale_id, created_by)
            logger.info(f"Sale created: {invoice_number}, total: {total_amount}")
            
            return {
                'sale_id': sale_id,
                'invoice_number': invoice_number,
                'total_amount': total_amount,
                'paid_amount': paid_amount,
                'remaining': remaining,
                'payment_status': payment_status,
            }
    
    def get_sale_with_items(self, sale_id: int) -> Optional[Dict]:
        """Get sale details with items."""
        sale = self.sale_repo.get_by_id(sale_id)
        if not sale:
            return None
        
        items = self.sale_repo.get_items(sale_id)
        sale['items'] = items
        return sale
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics."""
        return {
            'today_sales': self.sale_repo.get_today_total(),
            'today_sales_count': len(self.sale_repo.get_today_sales()),
            'total_revenue': self.sale_repo.get_total_revenue(),
            'total_sales_count': self.sale_repo.count(),
        }
