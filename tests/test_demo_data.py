import os
import tempfile

from app.database.connection import DatabaseManager
from app.database.migrations import MigrationManager
from app.repositories.product_repo import ProductRepository
from app.repositories.category_repo import CategoryRepository
from app.repositories.customer_repo import CustomerRepository
from app.repositories.supplier_repo import SupplierRepository
from app.repositories.sale_repo import SaleRepository
from app.repositories.purchase_repo import PurchaseRepository
from app.services.demo_data_service import DemoDataService


def test_supermarket_demo_data_populates_core_modules():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    try:
        db = DatabaseManager(path)
        db.initialize()
        migrations_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'migrations')
        MigrationManager(db, migrations_dir).apply_all()

        DemoDataService(db).generate_supermarket_data()

        assert ProductRepository(db).count() >= 18
        assert CategoryRepository(db).count() >= 5
        assert CustomerRepository(db).count() >= 5
        assert SupplierRepository(db).count() >= 3
        assert SaleRepository(db).count() >= 10
        assert PurchaseRepository(db).count() >= 4
        assert ProductRepository(db).total_stock_value() > 0
    finally:
        try:
            db.close()
        except Exception:
            pass
        for suffix in ('', '-wal', '-shm'):
            try:
                os.unlink(path + suffix)
            except OSError:
                pass
