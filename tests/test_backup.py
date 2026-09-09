"""
Tests for backup and restore functionality.
"""
import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import DatabaseManager
from app.database.migrations import MigrationManager
from app.services.backup_service import BackupService


@pytest.fixture
def db():
    """Create a temporary database with migrations applied."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    manager = DatabaseManager(db_path)
    manager.initialize()
    
    migrations_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'database', 'migrations'
    )
    migrator = MigrationManager(manager, migrations_dir)
    migrator.apply_all()
    
    # Add some test data
    manager.execute("INSERT INTO settings (key, value, category, updated_at) VALUES ('test_key', 'test_value', 'general', datetime('now'))")
    
    yield manager
    manager.close()
    
    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest.fixture
def backup_dir():
    """Create a temporary backup directory."""
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def backup_service(db, backup_dir):
    """Create a backup service for testing."""
    return BackupService(db, backup_dir)


class TestBackupService:
    """Tests for backup and restore functionality."""
    
    def test_create_backup(self, backup_service, backup_dir):
        """Test creating a backup."""
        success, path, error = backup_service.create_backup("test backup")
        
        assert success
        assert os.path.exists(path)
        assert error == ""
        assert os.path.getsize(path) > 0
    
    def test_backup_contains_data(self, backup_service, db):
        """Test that backup contains the original data."""
        success, path, error = backup_service.create_backup()
        assert success
        
        # Open backup and verify data
        backup_db = DatabaseManager(path)
        result = backup_db.fetch_one("SELECT * FROM settings WHERE key = 'test_key'")
        assert result is not None
        assert result['value'] == 'test_value'
        backup_db.close()
    
    def test_list_backups(self, backup_service):
        """Test listing backups."""
        # Create a few backups
        backup_service.create_backup("backup 1")
        backup_service.create_backup("backup 2")
        
        backups = backup_service.list_backups()
        assert len(backups) == 2
    
    def test_validate_backup(self, backup_service):
        """Test backup validation."""
        success, path, error = backup_service.create_backup()
        assert success
        
        is_valid, validation_error = backup_service.validate_backup(path)
        assert is_valid
        assert validation_error == ""
    
    def test_validate_nonexistent_file(self, backup_service):
        """Test validation of nonexistent file."""
        is_valid, error = backup_service.validate_backup("/nonexistent/path.db")
        assert not is_valid
        assert "does not exist" in error
    
    def test_validate_empty_file(self, backup_service, backup_dir):
        """Test validation of empty file."""
        empty_path = os.path.join(backup_dir, "empty.db")
        with open(empty_path, 'w') as f:
            pass  # Create empty file
        
        is_valid, error = backup_service.validate_backup(empty_path)
        assert not is_valid
        assert "empty" in error
    
    def test_restore_backup(self, backup_service, db):
        """Test restoring from backup."""
        # Create backup with current data
        success, backup_path, _ = backup_service.create_backup()
        assert success
        
        # Modify the database
        db.execute("INSERT INTO settings (key, value, category, updated_at) VALUES ('new_key', 'new_value', 'general', datetime('now'))")
        
        # Verify new data exists
        result = db.fetch_one("SELECT * FROM settings WHERE key = 'new_key'")
        assert result is not None
        
        # Restore backup
        success, error = backup_service.restore_backup(backup_path)
        assert success
        
        # Re-initialize connection after restore
        db.close()
        db._get_connection()
        
        # New data should be gone
        result = db.fetch_one("SELECT * FROM settings WHERE key = 'new_key'")
        assert result is None
        
        # Original data should still be there
        result = db.fetch_one("SELECT * FROM settings WHERE key = 'test_key'")
        assert result is not None
    
    def test_restore_nonexistent_backup(self, backup_service):
        """Test restoring from nonexistent backup."""
        success, error = backup_service.restore_backup("/nonexistent/backup.db")
        assert not success
        assert "not found" in error
    
    def test_delete_backup(self, backup_service):
        """Test deleting a backup."""
        success, path, _ = backup_service.create_backup()
        assert success
        assert os.path.exists(path)
        
        success, error = backup_service.delete_backup(path)
        assert success
        assert not os.path.exists(path)
    
    def test_cannot_delete_active_database(self, backup_service, db):
        """Test that active database cannot be deleted."""
        success, error = backup_service.delete_backup(db.db_path)
        assert not success
        assert "active database" in error
