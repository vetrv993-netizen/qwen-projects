"""
Database migration system.

Handles:
- Loading migration files from disk
- Tracking applied migrations
- Applying pending migrations in order
- Safe rollback (future enhancement)
"""
import os
import re
import logging
from typing import List, Optional, Tuple
from pathlib import Path

from .connection import DatabaseManager


logger = logging.getLogger(__name__)


class Migration:
    """Represents a single database migration."""
    
    def __init__(self, version: int, name: str, sql: str, filepath: str):
        self.version = version
        self.name = name
        self.sql = sql
        self.filepath = filepath
    
    def __repr__(self):
        return f"Migration(v{self.version}: {self.name})"


class MigrationManager:
    """
    Manages database schema migrations.
    
    Migrations are SQL files named like:
        001_initial.sql
        002_add_users.sql
        003_add_products.sql
    
    The manager:
    - Scans the migrations directory
    - Tracks which migrations have been applied
    - Applies pending migrations in order
    - Records each applied migration
    """
    
    # Pattern to match migration filenames
    MIGRATION_PATTERN = re.compile(r'^(\d+)_(\w+)\.sql$')
    
    def __init__(self, db: DatabaseManager, migrations_dir: str):
        """
        Initialize migration manager.
        
        Args:
            db: Database manager instance
            migrations_dir: Path to directory containing migration SQL files
        """
        self.db = db
        self.migrations_dir = migrations_dir
    
    def discover_migrations(self) -> List[Migration]:
        """
        Discover all migration files in the migrations directory.
        
        Returns:
            List of Migration objects sorted by version number
        """
        migrations = []
        
        if not os.path.exists(self.migrations_dir):
            logger.warning(f"Migrations directory not found: {self.migrations_dir}")
            return migrations
        
        for filename in sorted(os.listdir(self.migrations_dir)):
            match = self.MIGRATION_PATTERN.match(filename)
            if match:
                version = int(match.group(1))
                name = match.group(2)
                filepath = os.path.join(self.migrations_dir, filename)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    sql = f.read()
                
                migrations.append(Migration(version, name, sql, filepath))
        
        logger.debug(f"Discovered {len(migrations)} migration files")
        return migrations
    
    def get_applied_versions(self) -> List[int]:
        """
        Get list of already applied migration versions.
        
        Returns:
            List of version numbers
        """
        rows = self.db.fetch_all(
            "SELECT version FROM schema_version ORDER BY version"
        )
        return [row['version'] for row in rows]
    
    def current_version(self) -> int:
        """
        Get the current schema version.
        
        Returns:
            Current version number, or 0 if no migrations applied
        """
        versions = self.get_applied_versions()
        return max(versions) if versions else 0
    
    def get_pending_migrations(self) -> List[Migration]:
        """
        Get migrations that haven't been applied yet.
        
        Returns:
            List of pending Migration objects
        """
        all_migrations = self.discover_migrations()
        applied = set(self.get_applied_versions())
        
        pending = [m for m in all_migrations if m.version not in applied]
        pending.sort(key=lambda m: m.version)
        
        return pending
    
    def apply_migration(self, migration: Migration):
        """
        Apply a single migration.
        
        Args:
            migration: Migration to apply
        """
        logger.info(f"Applying migration v{migration.version}: {migration.name}")
        
        try:
            # Execute the migration SQL
            self.db.connection.executescript(migration.sql)
            
            # Record the migration
            self.db.execute(
                "INSERT INTO schema_version (version, name) VALUES (?, ?)",
                (migration.version, migration.name)
            )
            
            logger.info(f"Migration v{migration.version} applied successfully")
            
        except Exception as e:
            logger.error(f"Failed to apply migration v{migration.version}: {e}")
            raise
    
    def apply_all(self) -> int:
        """
        Apply all pending migrations.
        
        Returns:
            Number of migrations applied
        """
        pending = self.get_pending_migrations()
        
        if not pending:
            logger.info("No pending migrations")
            return 0
        
        logger.info(f"Found {len(pending)} pending migration(s)")
        
        applied_count = 0
        for migration in pending:
            self.apply_migration(migration)
            applied_count += 1
        
        logger.info(f"Applied {applied_count} migration(s). Current version: {self.current_version()}")
        return applied_count
    
    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate migration state.
        
        Checks:
        - No gaps in migration versions
        - All migration files are accounted for
        - Schema version table exists
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check schema_version table exists
        if not self.db.table_exists('schema_version'):
            errors.append("schema_version table does not exist")
            return False, errors
        
        # Check for gaps
        applied = self.get_applied_versions()
        all_migrations = self.discover_migrations()
        
        if all_migrations:
            expected_versions = set(m.version for m in all_migrations)
            applied_set = set(applied)
            
            # Check for applied migrations that don't have files
            orphaned = applied_set - expected_versions
            if orphaned:
                errors.append(f"Orphaned migration versions (no file): {orphaned}")
            
            # Check for version gaps
            if applied:
                for i in range(1, max(applied) + 1):
                    if i not in applied_set and i in expected_versions:
                        errors.append(f"Missing migration version: {i}")
        
        is_valid = len(errors) == 0
        return is_valid, errors
