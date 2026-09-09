"""
Logging configuration.

Sets up application-wide logging to both file and console.
"""
import os
import logging
import logging.handlers
from pathlib import Path


def setup_logging(log_dir: str, level: str = "INFO"):
    """
    Setup application logging.
    
    Creates:
    - File handler (rotating) in the log directory
    - Console handler for development
    
    Args:
        log_dir: Directory for log files
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    # Ensure log directory exists
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    log_file = os.path.join(log_dir, "app.log")
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler (rotating, max 5MB per file, keep 5 backups)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5,
        encoding='utf-8',
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler (for development)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger('PySide6').setLevel(logging.WARNING)
    logging.getLogger('shiboken').setLevel(logging.WARNING)
    
    root_logger.info("Logging initialized")
