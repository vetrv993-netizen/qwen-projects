"""
Application settings and configuration management.

Handles:
- Application data directory (%APPDATA%\\AccountingSystem)
- Database path
- Log directory
- Backup directory
- User preferences
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any


class AppSettings:
    """
    Application configuration manager.
    
    Stores user data in %APPDATA%\\AccountingSystem to ensure
    application updates never delete user data.
    """
    
    def __init__(self):
        """Initialize settings with default values."""
        # Application info
        self.app_name = "AccountingSystem"
        self.app_name_ar = "نظام المحاسبة"
        self.app_version = "1.0.0"
        self.organization_name = "AccountingSystem"
        
        # Base directories
        self._setup_directories()
        
        # Database
        self.db_path = os.path.join(self.data_dir, "app.db")
        
        # Logging
        self.log_dir = os.path.join(self.base_dir, "logs")
        self.log_file = os.path.join(self.log_dir, "app.log")
        self.log_level = "INFO"
        
        # Backup
        self.backup_dir = os.path.join(self.base_dir, "backups")
        
        # Export
        self.export_dir = os.path.join(self.base_dir, "exports")
        
        # User preferences (loaded from file)
        self._prefs_file = os.path.join(self.data_dir, "preferences.json")
        self._preferences = self._load_preferences()
        
        # Create directories
        self._ensure_directories()
    
    def _setup_directories(self):
        """Setup application directories in %APPDATA%."""
        # Use %APPDATA% on Windows, ~/.local/share on Linux/Mac
        if os.name == 'nt':
            appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
            self.base_dir = os.path.join(appdata, self.app_name)
        else:
            self.base_dir = os.path.join(
                os.path.expanduser('~'),
                '.local', 'share',
                self.app_name
            )
        
        self.data_dir = os.path.join(self.base_dir, 'data')
    
    def _ensure_directories(self):
        """Create all required directories if they don't exist."""
        directories = [
            self.base_dir,
            self.data_dir,
            self.log_dir,
            self.backup_dir,
            self.export_dir,
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def _load_preferences(self) -> Dict[str, Any]:
        """Load user preferences from file."""
        default_prefs = {
            'language': 'ar',
            'theme': 'light',
            'window_geometry': None,
            'last_user': None,
            'auto_backup': True,
            'backup_interval_days': 7,
        }
        
        if os.path.exists(self._prefs_file):
            try:
                with open(self._prefs_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    default_prefs.update(loaded)
            except (json.JSONDecodeError, IOError):
                pass
        
        return default_prefs
    
    def _save_preferences(self):
        """Save user preferences to file."""
        try:
            with open(self._prefs_file, 'w', encoding='utf-8') as f:
                json.dump(self._preferences, f, ensure_ascii=False, indent=2)
        except IOError as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to save preferences: {e}")
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference value."""
        return self._preferences.get(key, default)
    
    def set_preference(self, key: str, value: Any):
        """Set a user preference value and save to file."""
        self._preferences[key] = value
        self._save_preferences()
    
    @property
    def language(self) -> str:
        """Get current language setting."""
        return self.get_preference('language', 'ar')
    
    @language.setter
    def language(self, value: str):
        """Set language preference."""
        self.set_preference('language', value)
    
    @property
    def theme(self) -> str:
        """Get current theme setting."""
        return self.get_preference('theme', 'light')
    
    @theme.setter
    def theme(self, value: str):
        """Set theme preference."""
        self.set_preference('theme', value)
    
    def get_backup_path(self, filename: Optional[str] = None) -> str:
        """Get path for a backup file."""
        if filename is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backup_{timestamp}.db"
        return os.path.join(self.backup_dir, filename)
    
    def list_backups(self) -> list:
        """List all backup files."""
        if not os.path.exists(self.backup_dir):
            return []
        
        backups = []
        for filename in os.listdir(self.backup_dir):
            if filename.endswith('.db'):
                filepath = os.path.join(self.backup_dir, filename)
                stat = os.stat(filepath)
                backups.append({
                    'filename': filename,
                    'path': filepath,
                    'size': stat.st_size,
                    'modified': stat.st_mtime,
                })
        
        # Sort by modification time, newest first
        backups.sort(key=lambda x: x['modified'], reverse=True)
        return backups
