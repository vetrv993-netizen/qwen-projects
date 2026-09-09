import os
import tempfile


def test_ledger_tables_and_seed_accounts_exist():
    from app.database.connection import DatabaseManager
    from app.database.migrations import MigrationManager
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    try:
        db=DatabaseManager(path); db.initialize()
        migdir=os.path.join(os.path.dirname(os.path.dirname(__file__)),'database','migrations')
        MigrationManager(db,migdir).apply_all()
        accounts=db.fetch_all('SELECT code FROM accounts ORDER BY code')
        codes={x['code'] for x in accounts}
        assert {'1000','1010','1100','1200','2000','2100','4000','5000'} <= codes
        assert db.table_exists('journal_entries')
        assert db.table_exists('journal_lines')
        assert db.table_exists('payment_allocations')
    finally:
        try: db.close()
        except Exception: pass
        for suffix in ('','-wal','-shm'):
            try: os.unlink(path+suffix)
            except OSError: pass
