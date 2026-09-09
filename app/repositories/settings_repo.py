"""
Settings repository.

Handles all database operations for application settings.
"""
import logging
from typing import Optional, List, Dict
from datetime import datetime

from app.database.connection import DatabaseManager
from app.domain.models import AppSetting


logger = logging.getLogger(__name__)


class SettingsRepository:
    """
    Repository for application settings.
    
    Settings are stored as key-value pairs with categories.
    """
    
    def __init__(self, db: DatabaseManager):
        """
        Initialize settings repository.
        
        Args:
            db: Database manager instance
        """
        self.db = db
    
    def get(self, key: str) -> Optional[str]:
        """
        Get a setting value by key.
        
        Args:
            key: Setting key
            
        Returns:
            Setting value or None
        """
        row = self.db.fetch_one(
            "SELECT value FROM settings WHERE key = ?",
            (key,)
        )
        
        return row['value'] if row else None
    
    def set(self, key: str, value: str, category: str = 'general'):
        """
        Set a setting value. Creates the setting if it doesn't exist.
        
        Args:
            key: Setting key
            value: Setting value
            category: Setting category
        """
        now = datetime.now().isoformat()
        
        existing = self.get(key)
        
        if existing is not None:
            self.db.execute(
                "UPDATE settings SET value = ?, category = ?, updated_at = ? WHERE key = ?",
                (value, category, now, key)
            )
        else:
            self.db.insert('settings', {
                'key': key,
                'value': value,
                'category': category,
                'updated_at': now,
            })
    
    def delete(self, key: str) -> bool:
        """
        Delete a setting.
        
        Args:
            key: Setting key
            
        Returns:
            True if deleted
        """
        rows_affected = self.db.delete('settings', 'key = ?', (key,))
        return rows_affected > 0
    
    def get_all(self, category: Optional[str] = None) -> Dict[str, str]:
        """
        Get all settings, optionally filtered by category.
        
        Args:
            category: Optional category filter
            
        Returns:
            Dictionary of key-value pairs
        """
        if category:
            rows = self.db.fetch_all(
                "SELECT key, value FROM settings WHERE category = ?",
                (category,)
            )
        else:
            rows = self.db.fetch_all("SELECT key, value FROM settings")
        
        return {row['key']: row['value'] for row in rows}
    
    def get_by_category(self, category: str) -> List[AppSetting]:
        """
        Get all settings in a category.
        
        Args:
            category: Category name
            
        Returns:
            List of AppSetting objects
        """
        rows = self.db.fetch_all(
            "SELECT * FROM settings WHERE category = ? ORDER BY key",
            (category,)
        )
        
        return [
            AppSetting(
                id=row['id'],
                key=row['key'],
                value=row['value'],
                category=row['category'],
                updated_at=row['updated_at'],
            )
            for row in rows
        ]
    
    def get_default(self, key: str, default: str) -> str:
        """
        Get a setting value with a default fallback.
        
        Args:
            key: Setting key
            default: Default value if not found
            
        Returns:
            Setting value or default
        """
        value = self.get(key)
        return value if value is not None else default
    
    def get_int(self, key: str, default: int = 0) -> int:
        """
        Get a setting as an integer.
        
        Args:
            key: Setting key
            default: Default value
            
        Returns:
            Integer value
        """
        value = self.get(key)
        if value is not None:
            try:
                return int(value)
            except ValueError:
                pass
        return default
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """
        Get a setting as a float.
        
        Args:
            key: Setting key
            default: Default value
            
        Returns:
            Float value
        """
        value = self.get(key)
        if value is not None:
            try:
                return float(value)
            except ValueError:
                pass
        return default
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """
        Get a setting as a boolean.
        
        Args:
            key: Setting key
            default: Default value
            
        Returns:
            Boolean value
        """
        value = self.get(key)
        if value is not None:
            return value.lower() in ('1', 'true', 'yes', 'on')
        return default
    
    def initialize_defaults(self):
        """
        Initialize default settings if they don't exist.
        """
        defaults = {
            # Organization
            'org_name': ('المنشأة', 'organization'),
            'org_name_ar': ('المنشأة', 'organization'),
            'currency': ('SAR', 'organization'),
            'currency_symbol': ('ر.س', 'organization'),
            'tax_rate': ('15.0', 'organization'),
            
            # Display
            'language': ('ar', 'display'),
            'date_format': ('%Y-%m-%d', 'display'),
            'theme': ('light', 'display'),
            
            # Invoice
            'invoice_prefix': ('INV-', 'invoice'),
            'invoice_next_number': ('1', 'invoice'),
            
            # Backup
            'auto_backup': ('true', 'backup'),
            'backup_interval_days': ('7', 'backup'),
        }
        
        for key, (value, category) in defaults.items():
            if self.get(key) is None:
                self.set(key, value, category)
        
        logger.info("Default settings initialized")
