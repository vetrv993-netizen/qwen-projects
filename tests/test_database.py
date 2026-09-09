"""
Tests for database connection and operations.
"""
import os
import sys
import tempfile
import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import DatabaseManager


@pytest.fixture
def db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    manager = DatabaseManager(db_path)
    manager.initialize()
    yield manager
    manager.close()
    
    # Cleanup
    try:
        os.unlink(db_path)
    except OSError:
        pass


class TestDatabaseManager:
    """Tests for DatabaseManager."""
    
    def test_initialize(self, db):
        """Test database initialization creates schema_version table."""
        assert db.table_exists('schema_version')
    
    def test_execute(self, db):
        """Test SQL execution."""
        db.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
        db.execute("INSERT INTO test (name) VALUES (?)", ("test_value",))
        
        result = db.fetch_one("SELECT * FROM test WHERE name = ?", ("test_value",))
        assert result is not None
        assert result['name'] == 'test_value'
    
    def test_fetch_all(self, db):
        """Test fetching multiple rows."""
        db.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
        db.execute("INSERT INTO test (name) VALUES (?)", ("a",))
        db.execute("INSERT INTO test (name) VALUES (?)", ("b",))
        db.execute("INSERT INTO test (name) VALUES (?)", ("c",))
        
        results = db.fetch_all("SELECT * FROM test ORDER BY name")
        assert len(results) == 3
        assert results[0]['name'] == 'a'
        assert results[2]['name'] == 'c'
    
    def test_insert(self, db):
        """Test insert helper."""
        db.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT, value INTEGER)")
        
        row_id = db.insert('test', {'name': 'item1', 'value': 42})
        assert row_id > 0
        
        result = db.fetch_one("SELECT * FROM test WHERE id = ?", (row_id,))
        assert result['name'] == 'item1'
        assert result['value'] == 42
    
    def test_update(self, db):
        """Test update helper."""
        db.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
        row_id = db.insert('test', {'name': 'original'})
        
        affected = db.update('test', {'name': 'updated'}, 'id = ?', (row_id,))
        assert affected == 1
        
        result = db.fetch_one("SELECT * FROM test WHERE id = ?", (row_id,))
        assert result['name'] == 'updated'
    
    def test_delete(self, db):
        """Test delete helper."""
        db.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
        row_id = db.insert('test', {'name': 'to_delete'})
        
        affected = db.delete('test', 'id = ?', (row_id,))
        assert affected == 1
        
        result = db.fetch_one("SELECT * FROM test WHERE id = ?", (row_id,))
        assert result is None
    
    def test_transaction_commit(self, db):
        """Test successful transaction."""
        db.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
        
        with db.transaction():
            db.execute("INSERT INTO test (name) VALUES (?)", ("tx_item",))
        
        result = db.fetch_one("SELECT * FROM test WHERE name = ?", ("tx_item",))
        assert result is not None
    
    def test_transaction_rollback(self, db):
        """Test transaction rollback on error."""
        db.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
        
        try:
            with db.transaction():
                db.execute("INSERT INTO test (name) VALUES (?)", ("good",))
                db.execute("INSERT INTO test (name) VALUES (?)", (None,))  # Should fail
        except Exception:
            pass
        
        # The first insert should have been rolled back
        results = db.fetch_all("SELECT * FROM test")
        assert len(results) == 0
    
    def test_table_exists(self, db):
        """Test table existence check."""
        assert db.table_exists('schema_version')
        assert not db.table_exists('nonexistent_table')
    
    def test_foreign_keys(self, db):
        """Test foreign key enforcement."""
        db.execute("""
            CREATE TABLE parent (id INTEGER PRIMARY KEY, name TEXT)
        """)
        db.execute("""
            CREATE TABLE child (
                id INTEGER PRIMARY KEY, 
                parent_id INTEGER REFERENCES parent(id) ON DELETE CASCADE,
                name TEXT
            )
        """)
        
        parent_id = db.insert('parent', {'name': 'parent1'})
        db.insert('child', {'parent_id': parent_id, 'name': 'child1'})
        
        # Delete parent should cascade
        db.delete('parent', 'id = ?', (parent_id,))
        
        children = db.fetch_all("SELECT * FROM child")
        assert len(children) == 0
    
    def test_backup(self, db):
        """Test database backup."""
        db.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
        db.insert('test', {'name': 'backup_test'})
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            backup_path = f.name
        
        try:
            db.backup(backup_path)
            
            # Verify backup
            backup_db = DatabaseManager(backup_path)
            result = backup_db.fetch_one("SELECT * FROM test WHERE name = ?", ("backup_test",))
            assert result is not None
            backup_db.close()
        finally:
            os.unlink(backup_path)
    
    def test_get_size(self, db):
        """Test getting database file size."""
        size = db.get_size()
        assert size > 0
