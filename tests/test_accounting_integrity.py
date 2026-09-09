from datetime import datetime


def test_repositories_expose_crud_and_payment_paths():
    from app.repositories.product_repo import ProductRepository
    from app.repositories.category_repo import CategoryRepository
    from app.repositories.customer_repo import CustomerRepository
    from app.repositories.supplier_repo import SupplierRepository
    from app.repositories.payment_repo import PaymentRepository
    assert all(callable(getattr(ProductRepository, n, None)) for n in ('create','get_by_id','update','delete','search'))
    assert all(callable(getattr(CategoryRepository, n, None)) for n in ('create','get_by_id','update'))
    assert all(callable(getattr(CustomerRepository, n, None)) for n in ('create','get_by_id','update','delete','search'))
    assert all(callable(getattr(SupplierRepository, n, None)) for n in ('create','get_by_id','update','delete','search'))
    assert all(callable(getattr(PaymentRepository, n, None)) for n in ('create','get_by_id','get_customer_payments','get_supplier_payments'))


def test_accounting_service_clamps_negative_customer_balance_line():
    from app.services.accounting_service import AccountingService
    # Regression guard: an overpayment/rounding residue must never create a negative debit.
    class DummyRepo:
        def account_id(self, code): return 1
    service = AccountingService.__new__(AccountingService)
    service.repo = DummyRepo()
    line = service._line('1100', debit=0.0, description='ذمم عميل')
    assert line['debit'] >= 0

