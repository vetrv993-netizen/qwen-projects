import os
import tempfile

from app.database.connection import DatabaseManager
from app.database.migrations import MigrationManager
from app.repositories.product_repo import ProductRepository
from app.repositories.user_repo import UserRepository
from app.services.auth_service import AuthService
from app.services.reports_service import ReportsService
from app.services.purchase_service import PurchaseService
from app.services.sale_service import SaleService


def make_db():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    db = DatabaseManager(path)
    db.initialize()
    migrations_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'migrations')
    MigrationManager(db, migrations_dir).apply_all()
    return db, path


def cleanup(db, path):
    try:
        db.close()
    finally:
        for suffix in ('', '-wal', '-shm'):
            try: os.unlink(path + suffix)
            except OSError: pass


def test_login_success_for_demo_account():
    db, path = make_db()
    try:
        auth = AuthService(db)
        ok, user_id, err = auth.create_user('supermarket', 'سوبرماركت', 'demo123', 'admin')
        assert ok and user_id and not err
        success, user, session, error = auth.login('supermarket', 'demo123')
        assert success
        assert user.username == 'supermarket'
        assert session is not None
        assert error == ''
    finally:
        cleanup(db, path)


def test_low_stock_uses_selling_price_column():
    db, path = make_db()
    try:
        repo = ProductRepository(db)
        repo.create(name='Test', name_ar='اختبار', barcode='X', unit='piece', cost_price=10, selling_price=15, stock_quantity=2, min_stock=5)
        rows = ReportsService(db).low_stock()
        assert rows
        assert rows[0]['selling_price'] == 15
    finally:
        cleanup(db, path)


def test_purchase_preserves_lot_number_and_expiry():
    db, path = make_db()
    try:
        product_id = ProductRepository(db).create(name='P', name_ar='منتج', barcode='P1', unit='piece', cost_price=10, selling_price=20, stock_quantity=0, min_stock=1)
        result = PurchaseService(db).create_purchase([{
            'product_id': product_id, 'quantity': 5, 'unit_cost': 10, 'lot_number': 'LOT-TEST-01', 'expiry_date': '2030-01-01'
        }])
        lot = db.fetch_one('SELECT * FROM inventory_lots WHERE lot_number=?', ('LOT-TEST-01',))
        assert result['purchase_id'] > 0
        assert lot['expiry_date'] == '2030-01-01'
        assert lot['current_quantity'] == 5
        assert lot['branch_id'] == 1
    finally:
        cleanup(db, path)


def test_demo_style_opening_stock_is_sellable_through_a_lot():
    db, path = make_db()
    try:
        product_id = ProductRepository(db).create(name='P', name_ar='منتج', barcode='P2', unit='piece', cost_price=10, selling_price=20, stock_quantity=20, min_stock=1)
        db.insert('inventory_lots', {'product_id': product_id, 'branch_id': 1, 'lot_number': 'OPEN-TEST', 'expiry_date': None, 'unit_cost': 10, 'initial_quantity': 20, 'current_quantity': 20, 'received_at': '2030-01-01', 'is_active': 1, 'created_at': '2030-01-01', 'updated_at': '2030-01-01'})
        SaleService(db).create_sale([{'product_id': product_id, 'quantity': 2, 'unit_price': 20}])
        lot = db.fetch_one('SELECT current_quantity FROM inventory_lots WHERE lot_number=?', ('OPEN-TEST',))
        assert lot['current_quantity'] == 18
    finally:
        cleanup(db, path)
