from datetime import datetime, timedelta

from app.database.connection import DatabaseManager
from app.database.migrations import MigrationManager
from app.repositories.product_repo import ProductRepository
from app.repositories.lot_repo import LotRepository
from app.services.sale_service import SaleService


def make_db(tmp_path):
    db = DatabaseManager(str(tmp_path / 'test.db'))
    db.initialize()
    MigrationManager(db, 'database/migrations').apply_all()
    return db


def test_fefo_consumes_earliest_valid_expiry(tmp_path):
    db = make_db(tmp_path)
    products = ProductRepository(db)
    lots = LotRepository(db)
    p = products.create(name='Test', name_ar='اختبار', unit='piece', cost_price=10, selling_price=20, stock_quantity=15, min_stock=1)
    today = datetime.now()
    lots.create(product_id=p, lot_number='LATE', expiry_date=(today + timedelta(days=30)).strftime('%Y-%m-%d'), unit_cost=11, initial_quantity=5, current_quantity=5)
    lots.create(product_id=p, lot_number='EARLY', expiry_date=(today + timedelta(days=5)).strftime('%Y-%m-%d'), unit_cost=10, initial_quantity=10, current_quantity=10)

    result = SaleService(db).create_sale(items=[{'product_id': p, 'quantity': 7, 'unit_price': 20}], paid_amount=140)
    rows = db.fetch_all('SELECT il.lot_number, sil.quantity FROM sale_item_lots sil JOIN inventory_lots il ON il.id=sil.lot_id JOIN sale_items si ON si.id=sil.sale_item_id WHERE si.sale_id=? ORDER BY sil.id', (result['sale_id'],))
    assert rows[0]['lot_number'] == 'EARLY'
    assert rows[0]['quantity'] == 7
    assert lots.get_by_id(db.fetch_one("SELECT id FROM inventory_lots WHERE lot_number='EARLY'")['id'])['current_quantity'] == 3
