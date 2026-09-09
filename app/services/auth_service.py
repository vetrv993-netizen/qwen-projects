"""
Authentication service.

Handles:
- User login/logout
- Password verification
- Session management
- Default admin user creation
- Audit logging for auth events
"""
import uuid
import secrets
import logging
from typing import Optional, Tuple
from datetime import datetime, timedelta

from app.database.connection import DatabaseManager
from app.repositories.user_repo import UserRepository
from app.repositories.audit_repo import AuditRepository
from app.security.passwords import hash_password, verify_password
from app.domain.models import User, Session


logger = logging.getLogger(__name__)

# Session duration in hours
SESSION_DURATION_HOURS = 8


class AuthService:
    """
    Authentication and session management service.
    
    This service is the single entry point for all authentication
    operations. It coordinates between the user repository,
    password hashing, and session management.
    """
    
    def __init__(self, db: DatabaseManager):
        """
        Initialize auth service.
        
        Args:
            db: Database manager instance
        """
        self.db = db
        self.user_repo = UserRepository(db)
        self.audit_repo = AuditRepository(db)
    
    def login(self, username: str, password: str) -> Tuple[bool, Optional[User], Optional[Session], str]:
        """
        Authenticate a user and create a session.
        
        Args:
            username: Username
            password: Plain text password
            
        Returns:
            Tuple of (success, user, session, error_message)
        """
        # Find user
        user = self.user_repo.get_by_username(username)
        
        if user is None:
            self.audit_repo.log(
                user_id=0,
                username=username,
                action='login_failed',
                entity_type='auth',
                details='User not found',
            )
            logger.warning(f"Login failed: user '{username}' not found")
            return False, None, None, "اسم المستخدم أو كلمة المرور غير صحيحة"
        
        if not user.is_active:
            self.audit_repo.log(
                user_id=user.id,
                username=username,
                action='login_failed',
                entity_type='auth',
                details='Account deactivated',
            )
            logger.warning(f"Login failed: user '{username}' is deactivated")
            return False, None, None, "الحساب معطّل. يرجى مراجعة المدير."
        
        # Verify password
        if not verify_password(password, user.password_hash, user.salt):
            self.audit_repo.log(
                user_id=user.id,
                username=username,
                action='login_failed',
                entity_type='auth',
                details='Wrong password',
            )
            logger.warning(f"Login failed: wrong password for '{username}'")
            return False, None, None, "اسم المستخدم أو كلمة المرور غير صحيحة"
        
        # Create session
        session = self._create_session(user.id)
        
        # Update last login
        self.user_repo.update_last_login(user.id)
        
        # Audit log
        self.audit_repo.log(
            user_id=user.id,
            username=username,
            action='login',
            entity_type='auth',
            details=f'Session: {session.id}',
        )
        
        logger.info(f"User '{username}' logged in successfully")
        return True, user, session, ""
    
    def logout(self, session_id: str, user_id: int, username: str):
        """
        End a user session.
        
        Args:
            session_id: Session ID to end
            user_id: User ID
            username: Username (for audit)
        """
        self.db.execute(
            "UPDATE sessions SET is_active = 0 WHERE id = ?",
            (session_id,)
        )
        
        self.audit_repo.log(
            user_id=user_id,
            username=username,
            action='logout',
            entity_type='auth',
            details=f'Session: {session_id}',
        )
        
        logger.info(f"User '{username}' logged out")
    
    def validate_session(self, session_id: str) -> Optional[User]:
        """
        Validate a session and return the associated user.
        
        Args:
            session_id: Session ID to validate
            
        Returns:
            User if session is valid, None otherwise
        """
        row = self.db.fetch_one(
            """
            SELECT s.*, u.username, u.display_name, u.role, u.is_active 
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.id = ? AND s.is_active = 1
            """,
            (session_id,)
        )
        
        if row is None:
            return None
        
        # Check expiration
        expires_at = datetime.fromisoformat(row['expires_at'])
        if datetime.now() > expires_at:
            # Session expired
            self.db.execute(
                "UPDATE sessions SET is_active = 0 WHERE id = ?",
                (session_id,)
            )
            return None
        
        # Check user is still active
        if not row['is_active']:
            return None
        
        return User(
            id=row['user_id'],
            username=row['username'],
            display_name=row['display_name'],
            password_hash='',  # Not needed for validated session
            salt='',
            role=row['role'],
            is_active=True,
        )
    
    def create_user(
        self,
        username: str,
        display_name: str,
        password: str,
        role: str,
        created_by: Optional[int] = None,
    ) -> Tuple[bool, Optional[int], str]:
        """
        Create a new user.
        
        Args:
            username: Unique username
            display_name: Display name
            password: Plain text password (will be hashed)
            role: Role name
            created_by: ID of user creating this user
            
        Returns:
            Tuple of (success, user_id, error_message)
        """
        # Check username uniqueness
        if self.user_repo.exists(username):
            return False, None, "اسم المستخدم موجود مسبقاً"
        
        # Hash password
        hashed, salt = hash_password(password)
        
        # Create user
        user_id = self.user_repo.create(
            username=username,
            display_name=display_name,
            password_hash=hashed,
            salt=salt,
            role=role,
            created_by=created_by,
        )
        
        # Audit log
        if created_by:
            creator = self.user_repo.get_by_id(created_by)
            if creator:
                self.audit_repo.log(
                    user_id=created_by,
                    username=creator.username,
                    action='create_user',
                    entity_type='user',
                    entity_id=str(user_id),
                    details=f'Created user: {username}',
                )
        
        logger.info(f"User '{username}' created with role '{role}'")
        return True, user_id, ""
    
    def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str,
    ) -> Tuple[bool, str]:
        """
        Change a user's password.
        
        Args:
            user_id: User ID
            old_password: Current password for verification
            new_password: New password
            
        Returns:
            Tuple of (success, error_message)
        """
        user = self.user_repo.get_by_id(user_id)
        if user is None:
            return False, "المستخدم غير موجود"
        
        # Verify old password
        if not verify_password(old_password, user.password_hash, user.salt):
            return False, "كلمة المرور الحالية غير صحيحة"
        
        # Hash new password
        hashed, salt = hash_password(new_password)
        
        # Update
        self.user_repo.update(user_id, password_hash=hashed, salt=salt)
        
        # Audit log
        self.audit_repo.log(
            user_id=user_id,
            username=user.username,
            action='change_password',
            entity_type='user',
            entity_id=str(user_id),
        )
        
        logger.info(f"Password changed for user '{user.username}'")
        return True, ""
    
    def ensure_default_admin(self):
        """
        Ensure the default admin user exists.
        
        Creates a default admin user if no users exist in the database.
        This is for initial setup only.
        
        Default credentials:
            Username: admin
            Password: admin123
        
        WARNING: This should be changed immediately after first login!
        """
        count = self.user_repo.count(active_only=False)
        
        if count == 0:
            logger.info("No users found. Creating default admin user...")
            
            success, user_id, error = self.create_user(
                username='admin',
                display_name='مدير النظام',
                password='admin123',
                role='admin',
            )
            
            if success:
                logger.warning(
                    "Default admin user created. "
                    "Username: admin, Password: admin123. "
                    "CHANGE THIS IMMEDIATELY!"
                )
            else:
                logger.error(f"Failed to create default admin: {error}")
    
    def _create_session(self, user_id: int) -> Session:
        """
        Create a new session for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Session object
        """
        session_id = str(uuid.uuid4())
        token = secrets.token_hex(32)
        now = datetime.now()
        expires = now + timedelta(hours=SESSION_DURATION_HOURS)
        
        self.db.insert('sessions', {
            'id': session_id,
            'user_id': user_id,
            'token': token,
            'created_at': now.isoformat(),
            'expires_at': expires.isoformat(),
            'is_active': 1,
        })
        
        return Session(
            id=session_id,
            user_id=user_id,
            token=token,
            created_at=now.isoformat(),
            expires_at=expires.isoformat(),
            is_active=True,
        )
