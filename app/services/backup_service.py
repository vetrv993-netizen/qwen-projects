"""
Backup and restore service.

Handles:
- Creating database backups
- Restoring from backups
- Validating backup integrity
- Listing available backups
"""
import os
import shutil
import sqlite3
import logging
from typing import List, Optional, Tuple
from datetime import datetime
from pathlib import Path

from app.database.connection import DatabaseManager
from app.security.permission_enforcer import PermissionEnforcer, PermissionError
from app.security.permissions import Permission


logger = logging.getLogger(__name__)


class BackupService:
    """
    Database backup and restore service.
    
    Provides safe backup and restore operations that never
    destroy the active database during a failed restore.
    """
    
    def __init__(self, db: DatabaseManager, backup_dir: str, current_user_id: Optional[int] = None):
        """
        Initialize backup service.
        
        Args:
            db: Database manager instance
            backup_dir: Directory for storing backups
        """
        self.db = db
        # Initialize permission enforcer if user is provided
        self.current_user_id = current_user_id
        if current_user_id:
            self.enforcer = PermissionEnforcer(db, current_user_id)
        else:
            self.enforcer = None
        self.backup_dir = backup_dir
        
        # Ensure backup directory exists
        Path(backup_dir).mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, description: str = "") -> Tuple[bool, str, str]:
        """
        Create a backup of the current database.
        
        Args:
            description: Optional description for the backup
            
        Returns:
            Tuple of (success, backup_path, error_message)
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"backup_{timestamp}.db"
            backup_path = os.path.join(self.backup_dir, filename)
            
            # Use SQLite's backup API for safe backup
            self.db.backup(backup_path)
            
            # Create metadata file
            meta_path = backup_path + ".meta"
            with open(meta_path, 'w', encoding='utf-8') as f:
                f.write(f"created_at={datetime.now().isoformat()}\n")
                f.write(f"description={description}\n")
                f.write(f"source={self.db.db_path}\n")
                size = os.path.getsize(backup_path)
                f.write(f"size={size}\n")
            
            logger.info(f"Backup created: {backup_path} ({size} bytes)")
            return True, backup_path, ""
            
        except Exception as e:
            error_msg = f"Failed to create backup: {e}"
            logger.error(error_msg)
            return False, "", error_msg
    
    def restore_backup(self, backup_path: str) -> Tuple[bool, str]:
        """
        Restore the database from a backup.
        
        SAFETY: This method never destroys the active database.
        It first validates the backup, then creates a temporary
        copy, and only replaces the active database if validation passes.
        
        Args:
            backup_path: Path to the backup file
            
        Returns:
            Tuple of (success, error_message)
        """
        if not os.path.exists(backup_path):
            return False, f"Backup file not found: {backup_path}"
        
        try:
            # Step 1: Validate the backup
            is_valid, error = self.validate_backup(backup_path)
            if not is_valid:
                return False, f"Backup validation failed: {error}"
            
            # Step 2: Create a safety backup of the current database
            safety_path = self.db.db_path + ".pre_restore_backup"
            self.db.backup(safety_path)
            logger.info(f"Safety backup created: {safety_path}")
            
            # Step 3: Close current connection
            self.db.close()
            
            # Step 4: Copy backup to a temporary location
            temp_path = self.db.db_path + ".restoring"
            shutil.copy2(backup_path, temp_path)
            
            # Step 5: Validate the temporary copy
            try:
                test_conn = sqlite3.connect(temp_path)
                test_conn.execute("PRAGMA integrity_check")
                result = test_conn.execute("PRAGMA integrity_check").fetchone()
                test_conn.close()
                
                if result[0] != 'ok':
                    # Restore failed - clean up temp file
                    os.remove(temp_path)
                    return False, "Restored database failed integrity check"
                    
            except Exception as e:
                os.remove(temp_path)
                return False, f"Restored database is corrupted: {e}"
            
            # Step 6: Replace the active database
            shutil.move(temp_path, self.db.db_path)
            
            # Step 7: Remove WAL/SHM files if they exist
            wal_path = self.db.db_path + "-wal"
            shm_path = self.db.db_path + "-shm"
            if os.path.exists(wal_path):
                os.remove(wal_path)
            if os.path.exists(shm_path):
                os.remove(shm_path)
            
            logger.info(f"Database restored from: {backup_path}")
            return True, ""
            
        except Exception as e:
            error_msg = f"Restore failed: {e}"
            logger.error(error_msg)
            
            # Try to restore from safety backup if something went wrong
            safety_path = self.db.db_path + ".pre_restore_backup"
            if os.path.exists(safety_path):
                try:
                    shutil.copy2(safety_path, self.db.db_path)
                    logger.info("Restored from safety backup after failure")
                except Exception:
                    pass
            
            return False, error_msg
    
    def validate_backup(self, backup_path: str) -> Tuple[bool, str]:
        """
        Validate a backup file.
        
        Checks:
        - File exists and is readable
        - Is a valid SQLite database
        - Passes integrity check
        
        Args:
            backup_path: Path to the backup file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not os.path.exists(backup_path):
            return False, "File does not exist"
        
        if os.path.getsize(backup_path) == 0:
            return False, "File is empty"
        
        try:
            conn = sqlite3.connect(backup_path)
            
            # Check it's a valid SQLite database
            try:
                conn.execute("SELECT count(*) FROM sqlite_master")
            except sqlite3.DatabaseError:
                conn.close()
                return False, "Not a valid SQLite database"
            
            # Run integrity check
            result = conn.execute("PRAGMA integrity_check").fetchone()
            conn.close()
            
            if result[0] != 'ok':
                return False, f"Integrity check failed: {result[0]}"
            
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {e}"
    
    def list_backups(self) -> List[dict]:
        """
        List all available backups.
        
        Returns:
            List of backup info dictionaries
        """
        backups = []
        
        if not os.path.exists(self.backup_dir):
            return backups
        
        for filename in sorted(os.listdir(self.backup_dir), reverse=True):
            if filename.endswith('.db'):
                filepath = os.path.join(self.backup_dir, filename)
                stat = os.stat(filepath)
                
                # Try to read metadata
                meta = {}
                meta_path = filepath + ".meta"
                if os.path.exists(meta_path):
                    try:
                        with open(meta_path, 'r', encoding='utf-8') as f:
                            for line in f:
                                if '=' in line:
                                    key, value = line.strip().split('=', 1)
                                    meta[key] = value
                    except IOError:
                        pass
                
                backups.append({
                    'filename': filename,
                    'path': filepath,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'description': meta.get('description', ''),
                    'created_at': meta.get('created_at', ''),
                })
        
        return backups
    
    def delete_backup(self, backup_path: str) -> Tuple[bool, str]:
        """
        Delete a backup file.
        
        Args:
            backup_path: Path to the backup file
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            if not os.path.exists(backup_path):
                return False, "File not found"
            
            # Safety check: don't delete the active database
            if os.path.abspath(backup_path) == os.path.abspath(self.db.db_path):
                return False, "Cannot delete the active database"
            
            os.remove(backup_path)
            
            # Also remove metadata file if it exists
            meta_path = backup_path + ".meta"
            if os.path.exists(meta_path):
                os.remove(meta_path)
            
            logger.info(f"Backup deleted: {backup_path}")
            return True, ""
            
        except Exception as e:
            return False, f"Failed to delete backup: {e}"
