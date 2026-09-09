"""
SQLite database connection management.

Handles:
- Connection creation with proper settings
- WAL mode for better concurrency
- Foreign key enforcement
- Transaction management
- Connection pooling (simple)
"""
import sqlite3
import logging
import threading
from contextlib import contextmanager
from typing import Optional, List, Tuple, Any, Dict
from pathlib import Path


logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    SQLite database connection manager.
    
    Provides:
    - Thread-safe connection management
    - WAL mode for better read concurrency
    - Foreign key enforcement
    - Transaction context managers
    - Query execution helpers
    """
    
    def __init__(self, db_path: str):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._local = threading.local()
        
        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        Get thread-local database connection.
        
        Creates a new connection if one doesn't exist for this thread.
        """
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            conn = sqlite3.connect(
                self.db_path,
                timeout=30.0,
                isolation_level=None,  # We manage transactions manually
            )
            
            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode=WAL")
            
            # Enable foreign key enforcement
            conn.execute("PRAGMA foreign_keys=ON")
            
            # Set busy timeout
            conn.execute("PRAGMA busy_timeout=30000")
            
            # Optimize for reliability
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=-64000")  # 64MB cache
            conn.execute("PRAGMA temp_store=MEMORY")
            
            # Use row factory for dict-like access
            conn.row_factory = sqlite3.Row
            
            self._local.connection = conn
            logger.debug(f"Database connection created for thread {threading.current_thread().name}")
        
        return self._local.connection
    
    @property
    def connection(self) -> sqlite3.Connection:
        """Get the current thread's database connection."""
        return self._get_connection()
    
    def close(self):
        """Close the current thread's database connection."""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
            logger.debug("Database connection closed")
    
    def initialize(self):
        """
        Initialize the database.
        
        Creates the database file if it doesn't exist and
        sets up the schema_version table.
        """
        conn = self._get_connection()
        
        # Create schema_version table if it doesn't exist
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        
        conn.commit()
        logger.info(f"Database initialized at {self.db_path}")
    
    @contextmanager
    def transaction(self):
        """
        Context manager for database transactions.
        
        Usage:
            with db.transaction():
                db.execute("INSERT ...")
                db.execute("UPDATE ...")
        
        Automatically commits on success, rolls back on error.
        """
        conn = self._get_connection()
        conn.execute("BEGIN")
        try:
            yield conn
            conn.execute("COMMIT")
        except Exception as e:
            conn.execute("ROLLBACK")
            logger.error(f"Transaction failed, rolled back: {e}")
            raise
    
    def execute(self, sql: str, params: Tuple = ()) -> sqlite3.Cursor:
        """
        Execute a SQL statement.
        
        Args:
            sql: SQL statement to execute
            params: Query parameters
            
        Returns:
            Cursor object
        """
        conn = self._get_connection()
        try:
            return conn.execute(sql, params)
        except sqlite3.Error as e:
            logger.error(f"SQL execution error: {e}\nSQL: {sql}\nParams: {params}")
            raise
    
    def execute_many(self, sql: str, params_list: List[Tuple]) -> sqlite3.Cursor:
        """
        Execute a SQL statement multiple times with different parameters.
        
        Args:
            sql: SQL statement to execute
            params_list: List of parameter tuples
            
        Returns:
            Cursor object
        """
        conn = self._get_connection()
        try:
            return conn.executemany(sql, params_list)
        except sqlite3.Error as e:
            logger.error(f"SQL execution error: {e}\nSQL: {sql}")
            raise
    
    def fetch_one(self, sql: str, params: Tuple = ()) -> Optional[Dict[str, Any]]:
        """
        Execute a query and fetch one result.
        
        Args:
            sql: SQL query
            params: Query parameters
            
        Returns:
            Dictionary representing the row, or None
        """
        cursor = self.execute(sql, params)
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    def fetch_all(self, sql: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """
        Execute a query and fetch all results.
        
        Args:
            sql: SQL query
            params: Query parameters
            
        Returns:
            List of dictionaries representing rows
        """
        cursor = self.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """
        Insert a row into a table.
        
        Args:
            table: Table name
            data: Dictionary of column names and values
            
        Returns:
            Last inserted row ID
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        cursor = self.execute(sql, tuple(data.values()))
        return cursor.lastrowid
    
    def update(self, table: str, data: Dict[str, Any], where: str, params: Tuple = ()) -> int:
        """
        Update rows in a table.
        
        Args:
            table: Table name
            data: Dictionary of column names and values to update
            where: WHERE clause (without 'WHERE')
            params: Parameters for WHERE clause
            
        Returns:
            Number of rows affected
        """
        set_clause = ', '.join([f"{col} = ?" for col in data.keys()])
        sql = f"UPDATE {table} SET {set_clause} WHERE {where}"
        
        all_params = tuple(data.values()) + params
        cursor = self.execute(sql, all_params)
        return cursor.rowcount
    
    def delete(self, table: str, where: str, params: Tuple = ()) -> int:
        """
        Delete rows from a table.
        
        Args:
            table: Table name
            where: WHERE clause (without 'WHERE')
            params: Parameters for WHERE clause
            
        Returns:
            Number of rows affected
        """
        sql = f"DELETE FROM {table} WHERE {where}"
        cursor = self.execute(sql, params)
        return cursor.rowcount
    
    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists.
        
        Args:
            table_name: Name of the table
            
        Returns:
            True if table exists, False otherwise
        """
        result = self.fetch_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return result is not None
    
    def backup(self, backup_path: str):
        """
        Create a backup of the database.
        
        Args:
            backup_path: Path for the backup file
        """
        conn = self._get_connection()
        backup_conn = sqlite3.connect(backup_path)
        
        try:
            conn.backup(backup_conn)
            logger.info(f"Database backed up to {backup_path}")
        finally:
            backup_conn.close()
    
    def get_size(self) -> int:
        """
        Get the size of the database file in bytes.
        
        Returns:
            Size in bytes
        """
        if Path(self.db_path).exists():
            return Path(self.db_path).stat().st_size
        return 0
