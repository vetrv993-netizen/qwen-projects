"""
Tests for authentication and password hashing.
"""
import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import DatabaseManager
from app.database.migrations import MigrationManager
from app.security.passwords import hash_password, verify_password, validate_password_strength
from app.services.auth_service import AuthService
from app.repositories.user_repo import UserRepository


@pytest.fixture
def db():
    """Create a temporary database with migrations applied."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    manager = DatabaseManager(db_path)
    manager.initialize()
    
    # Apply migrations
    migrations_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'database', 'migrations'
    )
    migrator = MigrationManager(manager, migrations_dir)
    migrator.apply_all()
    
    yield manager
    manager.close()
    
    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest.fixture
def auth_service(db):
    """Create an auth service for testing."""
    return AuthService(db)


class TestPasswordHashing:
    """Tests for password hashing functions."""
    
    def test_hash_and_verify(self):
        """Test password hashing and verification."""
        password = "TestPassword123"
        hashed, salt = hash_password(password)
        
        assert hashed != password
        assert len(salt) == 64  # 32 bytes hex
        assert verify_password(password, hashed, salt)
    
    def test_wrong_password(self):
        """Test verification with wrong password."""
        password = "TestPassword123"
        hashed, salt = hash_password(password)
        
        assert not verify_password("WrongPassword", hashed, salt)
    
    def test_different_salts(self):
        """Test that same password with different salts produces different hashes."""
        password = "TestPassword123"
        hash1, salt1 = hash_password(password)
        hash2, salt2 = hash_password(password)
        
        assert salt1 != salt2
        assert hash1 != hash2
    
    def test_password_validation_strong(self):
        """Test strong password validation."""
        is_valid, error = validate_password_strength("StrongPass1")
        assert is_valid
        assert error == ""
    
    def test_password_validation_too_short(self):
        """Test password too short."""
        is_valid, error = validate_password_strength("Short1")
        assert not is_valid
        assert "8 characters" in error
    
    def test_password_validation_no_uppercase(self):
        """Test password without uppercase."""
        is_valid, error = validate_password_strength("lowercase1")
        assert not is_valid
        assert "uppercase" in error
    
    def test_password_validation_no_digit(self):
        """Test password without digit."""
        is_valid, error = validate_password_strength("NoDigitHere")
        assert not is_valid
        assert "digit" in error


class TestAuthService:
    """Tests for authentication service."""
    
    def test_create_user(self, auth_service):
        """Test user creation."""
        success, user_id, error = auth_service.create_user(
            username='testuser',
            display_name='Test User',
            password='TestPass123',
            role='cashier',
        )
        
        assert success
        assert user_id is not None
        assert error == ""
    
    def test_create_duplicate_user(self, auth_service):
        """Test creating user with duplicate username."""
        auth_service.create_user('duplicate', 'User 1', 'Pass1234', 'cashier')
        success, user_id, error = auth_service.create_user('duplicate', 'User 2', 'Pass1234', 'cashier')
        
        assert not success
        assert user_id is None
        assert "موجود" in error
    
    def test_login_success(self, auth_service):
        """Test successful login."""
        auth_service.create_user('loginuser', 'Login User', 'MyPass123', 'admin')
        
        success, user, session, error = auth_service.login('loginuser', 'MyPass123')
        
        assert success
        assert user is not None
        assert user.username == 'loginuser'
        assert session is not None
        assert error == ""
    
    def test_login_wrong_password(self, auth_service):
        """Test login with wrong password."""
        auth_service.create_user('loginuser2', 'Login User 2', 'CorrectPass1', 'cashier')
        
        success, user, session, error = auth_service.login('loginuser2', 'WrongPass')
        
        assert not success
        assert user is None
        assert session is None
    
    def test_login_nonexistent_user(self, auth_service):
        """Test login with nonexistent user."""
        success, user, session, error = auth_service.login('nobody', 'anypass')
        
        assert not success
        assert user is None
    
    def test_validate_session(self, auth_service):
        """Test session validation."""
        auth_service.create_user('sessionuser', 'Session User', 'Pass1234', 'manager')
        success, user, session, error = auth_service.login('sessionuser', 'Pass1234')
        
        validated_user = auth_service.validate_session(session.id)
        assert validated_user is not None
        assert validated_user.username == 'sessionuser'
    
    def test_logout(self, auth_service):
        """Test logout invalidates session."""
        auth_service.create_user('logoutuser', 'Logout User', 'Pass1234', 'cashier')
        success, user, session, error = auth_service.login('logoutuser', 'Pass1234')
        
        auth_service.logout(session.id, user.id, user.username)
        
        validated = auth_service.validate_session(session.id)
        assert validated is None
    
    def test_change_password(self, auth_service):
        """Test password change."""
        auth_service.create_user('chpwuser', 'Change PW User', 'OldPass123', 'cashier')
        success, user, _, _ = auth_service.login('chpwuser', 'OldPass123')
        
        # Change password
        changed, error = auth_service.change_password(user.id, 'OldPass123', 'NewPass456')
        assert changed
        assert error == ""
        
        # Old password should fail
        success2, _, _, _ = auth_service.login('chpwuser', 'OldPass123')
        assert not success2
        
        # New password should work
        success3, _, _, _ = auth_service.login('chpwuser', 'NewPass456')
        assert success3
    
    def test_ensure_default_admin(self, auth_service):
        """Test default admin creation."""
        auth_service.ensure_default_admin()
        
        # Should be able to login with default credentials
        success, user, session, error = auth_service.login('admin', 'admin123')
        assert success
        assert user.role == 'admin'
    
    def test_ensure_default_admin_idempotent(self, auth_service):
        """Test that ensure_default_admin doesn't create duplicates."""
        auth_service.ensure_default_admin()
        auth_service.ensure_default_admin()
        
        user_repo = UserRepository(auth_service.db)
        count = user_repo.count(active_only=False)
        assert count == 1  # Only one admin
