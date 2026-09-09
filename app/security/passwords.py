"""
Password hashing utilities.

Uses bcrypt for secure password hashing.
bcrypt was chosen because it has reliable prebuilt wheels for Windows
and doesn't require C++ compilation.
"""
import bcrypt
import secrets
import logging
from typing import Tuple


logger = logging.getLogger(__name__)


def generate_salt() -> str:
    """
    Generate a random salt for additional security.
    
    Note: bcrypt generates its own salt internally, but we store
    an additional application-level salt for defense in depth.
    
    Returns:
        Hex-encoded random salt string
    """
    return secrets.token_hex(32)


def hash_password(password: str, salt: str = None) -> Tuple[str, str]:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        salt: Optional application-level salt (generated if not provided)
        
    Returns:
        Tuple of (hashed_password, salt)
    """
    if salt is None:
        salt = generate_salt()
    
    # Combine application salt with password
    salted_password = f"{salt}{password}".encode('utf-8')
    
    # Hash with bcrypt (generates its own internal salt)
    hashed = bcrypt.hashpw(salted_password, bcrypt.gensalt(rounds=12))
    
    return hashed.decode('utf-8'), salt


def verify_password(password: str, hashed_password: str, salt: str) -> bool:
    """
    Verify a password against a stored hash.
    
    Args:
        password: Plain text password to verify
        hashed_password: Stored bcrypt hash
        salt: Application-level salt used during hashing
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        # Combine application salt with password
        salted_password = f"{salt}{password}".encode('utf-8')
        
        # Verify against stored hash
        return bcrypt.checkpw(salted_password, hashed_password.encode('utf-8'))
        
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password strength.
    
    Requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    
    return True, ""
