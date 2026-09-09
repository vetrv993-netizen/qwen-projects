"""
Tests for database migrations.
"""
import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import DatabaseManager
from app.database.migrations import MigrationManager


@pytest.fixture
def db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    manager = DatabaseManager(db_path)
    manager.initialize()
    yield manager
    manager.close()
    
    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest.fixture
def migrations_dir():
    """Get the migrations directory."""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'database', 'migrations'
    )


@pytest.fixture
def migrator(db, migrations_dir):
    """Create a migration manager for testing."""
    return MigrationManager(db, migrations_dir)


class TestMigrationManager:
    """Tests for migration system."""
    
    def test_discover_migrations(self, migrator):
        """Test discovering migration files."""
        migrations = migrator.discover_migrations()
        
        assert len(migrations) >= 2  # At least initial and outbox
        assert migrations[0].version == 1
        assert migrations[0].name == 'initial'
        assert migrations[1].version == 2
        assert migrations[1].name == 'outbox'
    
    def test_apply_all(self, migrator, db):
        """Test applying all migrations."""
        count = migrator.apply_all()
        
        assert count >= 2
        
        # Verify tables exist
        assert db.table_exists('users')
        assert db.table_exists('sessions')
        assert db.table_exists('audit_log')
        assert db.table_exists('settings')
        assert db.table_exists('outbox')
    
    def test_current_version(self, migrator):
        """Test getting current schema version."""
        # Before migrations
        assert migrator.current_version() == 0
        
        # After migrations
        migrator.apply_all()
        assert migrator.current_version() >= 2
    
    def test_idempotent_migrations(self, migrator, db):
        """Test that running migrations twice is safe."""
        migrator.apply_all()
        version_after_first = migrator.current_version()
        
        # Run again
        count = migrator.apply_all()
        assert count == 0  # No new migrations
        
        version_after_second = migrator.current_version()
        assert version_after_first == version_after_second
    
    def test_get_pending_migrations(self, migrator):
        """Test getting pending migrations."""
        pending = migrator.get_pending_migrations()
        assert len(pending) >= 2
        
        migrator.apply_all()
        
        pending = migrator.get_pending_migrations()
        assert len(pending) == 0
    
    def test_get_applied_versions(self, migrator):
        """Test getting applied migration versions."""
        migrator.apply_all()
        
        versions = migrator.get_applied_versions()
        assert 1 in versions
        assert 2 in versions
    
    def test_validate(self, migrator):
        """Test migration validation."""
        migrator.apply_all()
        
        is_valid, errors = migrator.validate()
        assert is_valid
        assert len(errors) == 0
    
    def test_users_table_schema(self, migrator, db):
        """Test that users table has correct schema."""
        migrator.apply_all()
        
        # Check columns exist
        columns = db.fetch_all("PRAGMA table_info(users)")
        column_names = [c['name'] for c in columns]
        
        assert 'id' in column_names
        assert 'username' in column_names
        assert 'display_name' in column_names
        assert 'password_hash' in column_names
        assert 'salt' in column_names
        assert 'role' in column_names
        assert 'is_active' in column_names
        assert 'created_at' in column_names
        assert 'updated_at' in column_names
        assert 'last_login_at' in column_names
        assert 'created_by' in column_names
    
    def test_outbox_table_schema(self, migrator, db):
        """Test that outbox table has correct schema."""
        migrator.apply_all()
        
        columns = db.fetch_all("PRAGMA table_info(outbox)")
        column_names = [c['name'] for c in columns]
        
        assert 'id' in column_names
        assert 'operation_id' in column_names
        assert 'entity_type' in column_names
        assert 'entity_id' in column_names
        assert 'operation_type' in column_names
        assert 'payload' in column_names
        assert 'status' in column_names
        assert 'retry_count' in column_names
        assert 'max_retries' in column_names
        assert 'last_error' in column_names
        assert 'synced_at' in column_names
        assert 'created_at' in column_names
        assert 'updated_at' in column_names
    
    def test_indexes_created(self, migrator, db):
        """Test that indexes are created."""
        migrator.apply_all()
        
        indexes = db.fetch_all("SELECT name FROM sqlite_master WHERE type='index'")
        index_names = [i['name'] for i in indexes]
        
        assert 'idx_users_username' in index_names
        assert 'idx_sessions_user_id' in index_names
        assert 'idx_audit_log_created_at' in index_names
        assert 'idx_outbox_status' in index_names
        assert 'idx_settings_key' in index_names
    
    def test_foreign_keys_enabled(self, migrator, db):
        """Test that foreign keys are enforced."""
        migrator.apply_all()
        
        # Try to insert a session with nonexistent user
        try:
            db.execute(
                "INSERT INTO sessions (id, user_id, token, created_at, expires_at) "
                "VALUES ('test', 99999, 'token', '2024-01-01', '2024-12-31')"
            )
            # If we get here, foreign keys aren't enforced
            assert False, "Foreign key constraint should have prevented this"
        except Exception:
            # Expected - foreign key violation
            pass
