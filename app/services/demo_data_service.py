"""
Demo data service - generates realistic demo data for different business types.
"""
import logging
from typing import Dict, Any
from datetime import datetime, timedelta
import random

from app.database.connection import DatabaseManager
from app.repositories.product_repo import ProductRepository
from app.repositories.category_repo import CategoryRepository
from app.repositories.customer_repo import CustomerRepository
from app.repositories.supplier_repo import SupplierRepository
from app.services.sale_service import SaleService
from app.services.purchase_service import PurchaseService


logger = logging.getLogger(__name__)


class DemoDataService:
    """Generates realistic demo data for different business types."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.product_repo = ProductRepository(db)
        self.category_repo = CategoryRepository(db)
        self.customer_repo = CustomerRepository(db)
        self.supplier_repo = SupplierRepository(db)
        self.sale_service = SaleService(db)
        self.purchase_service = PurchaseService(db)

    def _current_branch_id(self):
        row = self.db.fetch_one("SELECT value FROM settings WHERE key='current_branch_id' LIMIT 1")
        try:
            return int(row['value']) if row and row.get('value') else None
        except (TypeError, ValueError):
            return None
    
    def generate_supermarket_data(self):
        """Generate realistic supermarket demo data."""
        logger.info("Generating supermarket demo data...")
        
        # Categories
        categories = [
            ('Groceries', 'بقالة'),
            ('Beverages', 'مشروبات'),
            ('Dairy', 'ألبان'),
            ('Household', 'منزلية'),
            ('Personal Care', 'عناية شخصية'),
        ]
        
        category_ids = {}
        for name_en, name_ar in categories:
            cat_id = self.category_repo.create(
                name=name_en,
                name_ar=name_ar,
                sort_order=len(category_ids)
            )
            category_ids[name_en] = cat_id
        
        # Products
        products_data = [
            # Groceries
            ('Rice Basmati', 'أرز بسمتي', category_ids['Groceries'], 'kg', 800, 1000, '0421000001'),
            ('Sugar', 'سكر', category_ids['Groceries'], 'kg', 300, 400, '0421000002'),
            ('Flour', 'دقيق', category_ids['Groceries'], 'kg', 200, 280, '0421000003'),
            ('Oil Sunflower', 'زيت دوار الشمس', category_ids['Groceries'], 'liter', 1200, 1500, '0421000004'),
            ('Pasta', 'معكرونة', category_ids['Groceries'], 'pack', 150, 220, '0421000005'),
            
            # Beverages
            ('Water 1.5L', 'ماء 1.5 لتر', category_ids['Beverages'], 'bottle', 80, 120, '0422000001'),
            ('Juice Orange', 'عصير برتقال', category_ids['Beverages'], 'liter', 350, 500, '0422000002'),
            ('Tea Black', 'شاي أسود', category_ids['Beverages'], 'pack', 250, 380, '0422000003'),
            ('Coffee Instant', 'قهوة سريعة', category_ids['Beverages'], 'jar', 800, 1200, '0422000004'),
            
            # Dairy
            ('Milk Fresh', 'حليب طازج', category_ids['Dairy'], 'liter', 280, 400, '0423000001'),
            ('Yogurt', 'زبادي', category_ids['Dairy'], 'cup', 120, 180, '0423000002'),
            ('Cheese White', 'جبنة بيضاء', category_ids['Dairy'], 'kg', 1500, 2200, '0423000003'),
            
            # Household
            ('Dish Soap', 'صابون جلي', category_ids['Household'], 'bottle', 250, 380, '0424000001'),
            ('Laundry Detergent', 'منظف غسيل', category_ids['Household'], 'kg', 450, 650, '0424000002'),
            ('Tissue Paper', 'مناديل ورقية', category_ids['Household'], 'pack', 180, 280, '0424000003'),
            
            # Personal Care
            ('Shampoo', 'شامبو', category_ids['Personal Care'], 'bottle', 350, 520, '0425000001'),
            ('Soap Bar', 'صابون', category_ids['Personal Care'], 'piece', 80, 130, '0425000002'),
            ('Toothpaste', 'معجون أسنان', category_ids['Personal Care'], 'tube', 220, 350, '0425000003'),
        ]
        
        product_ids = {}
        for name_en, name_ar, cat_id, unit, cost, price, barcode in products_data:
            prod_id = self.product_repo.create(
                barcode=barcode,
                name=name_en,
                name_ar=name_ar,
                category_id=cat_id,
                unit=unit,
                cost_price=cost,
                selling_price=price,
                stock_quantity=random.randint(20, 100),
                min_stock=10,
            )
            product_ids[name_en] = prod_id
            opening_qty = self.product_repo.get_by_id(prod_id)['stock_quantity'] or 0
            if opening_qty > 0:
                self.db.insert('inventory_lots', {
                    'product_id': prod_id, 'branch_id': self._current_branch_id(),
                    'lot_number': f'OPEN-{prod_id}', 'expiry_date': None,
                    'unit_cost': cost, 'initial_quantity': opening_qty,
                    'current_quantity': opening_qty,
                    'received_at': datetime.now().isoformat(), 'is_active': 1,
                    'created_at': datetime.now().isoformat(), 'updated_at': datetime.now().isoformat()
                })
        
        # Customers
        customers_data = [
            ('Ahmed Al-Houthi', 'أحمد الحوثي', '771234567'),
            ('Fatima Al-Shami', 'فاطمة الشامي', '772345678'),
            ('Mohammed Al-Qadi', 'محمد القاضي', '773456789'),
            ('Sara Al-Ansi', 'سارة الأنسي', '774567890'),
            ('Ali Al-Hajri', 'علي الحجري', '775678901'),
        ]
        
        for name_en, name_ar, phone in customers_data:
            self.customer_repo.create(
                name=name_en,
                name_ar=name_ar,
                phone=phone,
                balance=0,
            )
        
        # Suppliers
        suppliers_data = [
            ('Yemen Food Co.', 'شركة اليمن للغذاء', '771111111'),
            ('Al-Saeed Trading', 'تجارة السعيد', '772222222'),
            ('Modern Supplies', 'المؤن الحديثة', '773333333'),
        ]
        
        for name_en, name_ar, phone in suppliers_data:
            self.supplier_repo.create(
                name=name_en,
                name_ar=name_ar,
                phone=phone,
                balance=0,
            )
        
        # Generate some purchases first so the Purchases and Inventory pages
        # have realistic inbound movements to display.
        all_products = self.product_repo.get_all()
        all_suppliers = self.supplier_repo.get_all()
        for _ in range(4):
            supplier_id = all_suppliers[_ % len(all_suppliers)]['id'] if all_suppliers else None
            items = []
            for product in random.sample(all_products, min(4, len(all_products))):
                items.append({
                    'product_id': product['id'],
                    'quantity': random.randint(5, 20),
                    'unit_cost': product['cost_price'],
                    'discount': 0,
                })
            if items:
                try:
                    self.purchase_service.create_purchase(
                        items=items,
                        supplier_id=supplier_id,
                        paid_amount=0,
                        payment_method='cash',
                    )
                except Exception as e:
                    logger.warning(f"Failed to create demo purchase: {e}")

        # Generate 10 reliable demo sales. Keep each sale on distinct products
        # and use small quantities so the generated dataset is deterministic enough
        # to exercise the sales flow without random stock exhaustion.
        all_products = self.product_repo.get_all()
        for sale_index in range(10):
            candidates = all_products[sale_index % len(all_products):] + all_products[:sale_index % len(all_products)]
            items = []
            for product in candidates[:3]:
                items.append({
                    'product_id': product['id'],
                    'quantity': 1,
                    'unit_price': product['selling_price'],
                    'discount': 0,
                })
            try:
                total_paid = sum(i['unit_price'] * i['quantity'] for i in items)
                self.sale_service.create_sale(
                    items=items,
                    paid_amount=total_paid,
                    payment_method='cash',
                )
            except Exception as e:
                logger.warning(f"Failed to create demo sale #{sale_index + 1}: {e}")
        
        logger.info("Supermarket demo data generated successfully")
    
    def generate_pharmacy_data(self):
        """Generate realistic pharmacy demo data."""
        logger.info("Generating pharmacy demo data...")
        
        # Categories
        categories = [
            ('Medicines', 'أدوية'),
            ('Medical Supplies', 'مستلزمات طبية'),
            ('Vitamins', 'فيتامينات'),
            ('Baby Care', 'عناية بالأطفال'),
        ]
        
        category_ids = {}
        for name_en, name_ar in categories:
            cat_id = self.category_repo.create(
                name=name_en,
                name_ar=name_ar,
                sort_order=len(category_ids)
            )
            category_ids[name_en] = cat_id
        
        # Products with expiry dates
        products_data = [
            ('Paracetamol 500mg', 'باراسيتامول 500mg', category_ids['Medicines'], 'box', 350, 500, 'PH001', 180),
            ('Amoxicillin 500mg', 'أموكسيسيلين 500mg', category_ids['Medicines'], 'box', 800, 1200, 'PH002', 240),
            ('Ibuprofen 400mg', 'إيبوبروفين 400mg', category_ids['Medicines'], 'box', 450, 650, 'PH003', 200),
            ('Vitamin C 1000mg', 'فيتامين سي 1000mg', category_ids['Vitamins'], 'bottle', 1200, 1800, 'PH004', 365),
            ('Multivitamin', 'فيتامينات متعددة', category_ids['Vitamins'], 'bottle', 2500, 3500, 'PH005', 300),
            ('Face Mask N95', 'كمامة N95', category_ids['Medical Supplies'], 'box', 1500, 2200, 'PH006', 730),
            ('Hand Sanitizer', 'معقم يدين', category_ids['Medical Supplies'], 'bottle', 600, 900, 'PH007', 500),
            ('Baby Diapers', 'حفاضات أطفال', category_ids['Baby Care'], 'pack', 3500, 4800, 'PH008', 400),
            ('Baby Formula', 'حليب أطفال', category_ids['Baby Care'], 'can', 8000, 11000, 'PH009', 280),
        ]
        
        for name_en, name_ar, cat_id, unit, cost, price, barcode, shelf_days in products_data:
            expiry = (datetime.now() + timedelta(days=shelf_days)).strftime('%Y-%m-%d')
            stock_qty = random.randint(15, 80)
            product_id = self.product_repo.create(
                barcode=barcode,
                name=name_en,
                name_ar=name_ar,
                category_id=cat_id,
                unit=unit,
                cost_price=cost,
                selling_price=price,
                stock_quantity=stock_qty,
                min_stock=10,
                expiry_date=expiry,
            )
            try:
                self.db.insert('inventory_lots', {
                    'product_id': product_id, 'branch_id': None, 'lot_number': f'OPEN-{product_id}',
                    'expiry_date': expiry, 'unit_cost': cost, 'initial_quantity': stock_qty,
                    'current_quantity': stock_qty, 'received_at': datetime.now().isoformat(),
                    'is_active': 1, 'created_at': datetime.now().isoformat(), 'updated_at': datetime.now().isoformat()
                })
            except Exception:
                logger.exception('Failed to create opening pharmacy lot for %s', name_ar)
        
        # Customers
        customers_data = [
            ('Khalid Al-Tamimi', 'خالد التميمي', '776789012'),
            ('Nora Al-Zubairi', 'نورة الزبيري', '777890123'),
            ('Omar Al-Sharafi', 'عمر الشرفي', '778901234'),
        ]
        
        for name_en, name_ar, phone in customers_data:
            self.customer_repo.create(
                name=name_en,
                name_ar=name_ar,
                phone=phone,
                balance=0,
            )
        
        # Suppliers
        suppliers_data = [
            ('Yemen Pharma', 'فارما اليمن', '774444444'),
            ('Medical Trust', 'الثقة الطبية', '775555555'),
        ]
        
        for name_en, name_ar, phone in suppliers_data:
            self.supplier_repo.create(
                name=name_en,
                name_ar=name_ar,
                phone=phone,
                balance=0,
            )
        
        logger.info("Pharmacy demo data generated successfully")
    
    def generate_restaurant_data(self):
        """Generate realistic restaurant demo data."""
        logger.info("Generating restaurant demo data...")
        
        # Categories
        categories = [
            ('Main Dishes', 'أطباق رئيسية'),
            ('Appetizers', 'مقبلات'),
            ('Beverages', 'مشروبات'),
            ('Desserts', 'حلويات'),
        ]
        
        category_ids = {}
        for name_en, name_ar in categories:
            cat_id = self.category_repo.create(
                name=name_en,
                name_ar=name_ar,
                sort_order=len(category_ids)
            )
            category_ids[name_en] = cat_id
        
        # Menu items
        products_data = [
            ('Mandi Chicken', 'مندي دجاج', category_ids['Main Dishes'], 'plate', 1500, 2500, 'R001'),
            ('Mandi Lamb', 'مندي لحم', category_ids['Main Dishes'], 'plate', 2000, 3200, 'R002'),
            ('Kabsa', 'كبسة', category_ids['Main Dishes'], 'plate', 1200, 2000, 'R003'),
            ('Grilled Chicken', 'دجاج مشوي', category_ids['Main Dishes'], 'plate', 1300, 2200, 'R004'),
            ('Hummus', 'حمص', category_ids['Appetizers'], 'plate', 300, 500, 'R005'),
            ('Fattoush', 'فتوش', category_ids['Appetizers'], 'plate', 350, 550, 'R006'),
            ('Fresh Juice', 'عصير طازج', category_ids['Beverages'], 'glass', 150, 300, 'R007'),
            ('Tea', 'شاي', category_ids['Beverages'], 'cup', 50, 100, 'R008'),
            ('Coffee', 'قهوة', category_ids['Beverages'], 'cup', 80, 150, 'R009'),
            ('Kunafa', 'كنافة', category_ids['Desserts'], 'plate', 400, 700, 'R010'),
        ]
        
        for name_en, name_ar, cat_id, unit, cost, price, barcode in products_data:
            self.product_repo.create(
                barcode=barcode,
                name=name_en,
                name_ar=name_ar,
                category_id=cat_id,
                unit=unit,
                cost_price=cost,
                selling_price=price,
                stock_quantity=100,
                min_stock=20,
            )
        
        # Customers (regular customers)
        customers_data = [
            ('Abdullah Al-Hakimi', 'عبدالله الحكيمي', '779012345'),
            ('Layla Al-Mutawakil', 'ليلى المتوكل', '780123456'),
        ]
        
        for name_en, name_ar, phone in customers_data:
            self.customer_repo.create(
                name=name_en,
                name_ar=name_ar,
                phone=phone,
                balance=0,
            )
        
        # Suppliers
        suppliers_data = [
            ('Fresh Foods Yemen', 'أغذية طازجة اليمن', '776666666'),
        ]
        
        for name_en, name_ar, phone in suppliers_data:
            self.supplier_repo.create(
                name=name_en,
                name_ar=name_ar,
                phone=phone,
                balance=0,
            )
        
        logger.info("Restaurant demo data generated successfully")
    
    def generate_hotel_data(self):
        """Generate realistic hotel demo data."""
        logger.info("Generating hotel demo data...")
        
        # Categories (room types and services)
        categories = [
            ('Rooms', 'غرف'),
            ('Services', 'خدمات'),
            ('Food & Beverage', 'مأكولات ومشروبات'),
        ]
        
        category_ids = {}
        for name_en, name_ar in categories:
            cat_id = self.category_repo.create(
                name=name_en,
                name_ar=name_ar,
                sort_order=len(category_ids)
            )
            category_ids[name_en] = cat_id
        
        # Room types and services
        products_data = [
            ('Single Room', 'غرفة مفردة', category_ids['Rooms'], 'night', 8000, 15000, 'H001'),
            ('Double Room', 'غرفة مزدوجة', category_ids['Rooms'], 'night', 12000, 22000, 'H002'),
            ('Suite', 'جناح', category_ids['Rooms'], 'night', 25000, 45000, 'H003'),
            ('Laundry Service', 'خدمة غسيل', category_ids['Services'], 'service', 500, 1000, 'H004'),
            ('Airport Transfer', 'نقل مطار', category_ids['Services'], 'trip', 3000, 5000, 'H005'),
            ('Breakfast', 'فطور', category_ids['Food & Beverage'], 'person', 800, 1500, 'H006'),
            ('Lunch Buffet', 'بوفيه غداء', category_ids['Food & Beverage'], 'person', 1500, 2800, 'H007'),
            ('Dinner', 'عشاء', category_ids['Food & Beverage'], 'person', 2000, 3500, 'H008'),
        ]
        
        for name_en, name_ar, cat_id, unit, cost, price, barcode in products_data:
            self.product_repo.create(
                barcode=barcode,
                name=name_en,
                name_ar=name_ar,
                category_id=cat_id,
                unit=unit,
                cost_price=cost,
                selling_price=price,
                stock_quantity=100,
                min_stock=0,
            )
        
        # Customers (guests)
        customers_data = [
            ('Hassan Al-Eryani', 'حسن الإرياني', '781234567'),
            ('Maryam Al-Hashimi', 'مريم الهاشمي', '782345678'),
            ('Yousef Al-Wazir', 'يوسف الوزير', '783456789'),
        ]
        
        for name_en, name_ar, phone in customers_data:
            self.customer_repo.create(
                name=name_en,
                name_ar=name_ar,
                phone=phone,
                balance=0,
            )
        
        # Suppliers
        suppliers_data = [
            ('Hotel Supplies Co.', 'شركة مستلزمات الفنادق', '777777777'),
            ('Premium Linens', 'مفروشات فاخرة', '778888888'),
        ]
        
        for name_en, name_ar, phone in suppliers_data:
            self.supplier_repo.create(
                name=name_en,
                name_ar=name_ar,
                phone=phone,
                balance=0,
            )
        
        logger.info("Hotel demo data generated successfully")
