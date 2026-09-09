#!/usr/bin/env python3
"""
نظام المحاسبة وإدارة الأعمال — Accounting & Business Management System
Main entry point for the desktop application.

Usage:
    python main.py
"""
import sys
import os

# Ensure the project root is on the Python path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.utils.logging_config import setup_logging
from app.config.settings import AppSettings
from app.database.connection import DatabaseManager
from app.database.migrations import MigrationManager
from app.ui.main_window import MainWindow
from app.ui.login_window import LoginWindow

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QLocale, QThread, Signal
from PySide6.QtGui import QFont


class DemoDataWorker(QThread):
    """Generate demo data off the Qt UI thread after login."""

    finished_ok = Signal(str)
    failed = Signal(str)

    def __init__(self, db_path, business_type, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.business_type = business_type

    def run(self):
        worker_db = None
        try:
            from app.repositories.product_repo import ProductRepository
            from app.services.demo_data_service import DemoDataService

            # IMPORTANT: DatabaseManager uses thread-local SQLite connections.
            # Never share the GUI thread's connection with this worker.
            worker_db = DatabaseManager(self.db_path)
            worker_db.initialize()

            product_repo = ProductRepository(worker_db)
            if product_repo.count() > 0:
                self.finished_ok.emit('already_populated')
                return

            service = DemoDataService(worker_db)
            generators = {
                'supermarket': service.generate_supermarket_data,
                'pharmacy': service.generate_pharmacy_data,
                'restaurant': service.generate_restaurant_data,
                'hotel': service.generate_hotel_data,
            }
            generator = generators.get(self.business_type)
            if generator:
                generator()
            self.finished_ok.emit(self.business_type)
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            if worker_db is not None:
                worker_db.close()


def main():
    """Application entry point."""
    # 1. Initialize configuration
    settings = AppSettings()
    
    # 2. Setup logging
    setup_logging(settings.log_dir)
    
    import logging
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Application starting...")
    logger.info(f"Version: {settings.app_version}")
    logger.info(f"Data directory: {settings.data_dir}")
    logger.info("=" * 60)
    
    # 3. Initialize database
    db = DatabaseManager(settings.db_path)
    db.initialize()
    logger.info("Database initialized successfully")
    
    # 4. Run migrations
    migrations_dir = os.path.join(PROJECT_ROOT, "database", "migrations")
    migrator = MigrationManager(db, migrations_dir)
    migrator.apply_all()
    logger.info(f"Database schema version: {migrator.current_version()}")
    
    # 5. Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName(settings.app_name)
    app.setApplicationVersion(settings.app_version)
    app.setOrganizationName(settings.organization_name)
    
    # Set RTL for Arabic
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    
    # Set Arabic-friendly font
    font = QFont("Segoe UI", 10)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)
    
    # Set application icon
    icon_paths = []
    if hasattr(sys, '_MEIPASS'):
        icon_paths.append(os.path.join(sys._MEIPASS, 'assets', 'icon.ico'))
    icon_paths.append(os.path.join(PROJECT_ROOT, 'assets', 'icon.ico'))
    
    for icon_path in icon_paths:
        if os.path.exists(icon_path):
            from PySide6.QtGui import QIcon
            icon = QIcon(icon_path)
            if not icon.isNull():
                app.setWindowIcon(icon)
                logger.info(f"Application icon set from: {icon_path}")
                break
    else:
        logger.info("No icon file found, using system default")
    
    # 6. Show login window, then main window on success
    from app.services.auth_service import AuthService
    auth_service = AuthService(db)
    
    login_window = LoginWindow(auth_service, settings)
    
    def on_login_success(user, business_type):
        # Authentication has already succeeded at this point. Build the main
        # window before closing login, and keep login visible if UI startup fails
        # so the user never gets a misleading "login failed" impression.
        try:
            main_window = MainWindow(db, auth_service, user, settings, business_type)
        except Exception as exc:
            logger.exception("Post-login UI initialization failed for user '%s'", user.username)
            login_window._show_error("تم تسجيل الدخول بنجاح، لكن تعذر فتح النظام. تم إبقاء شاشة الدخول مفتوحة.")
            login_window.login_button.setEnabled(True)
            login_window.login_button.setText("دخول")
            return
        app._main_window = main_window
        main_window.show()
        login_window.close()

        # Demo data is intentionally generated after the main window is visible
        # and on a worker thread so login never appears frozen.
        demo_accounts = {'supermarket', 'pharmacy', 'restaurant', 'hotel'}
        if user.username in demo_accounts:
            worker = DemoDataWorker(settings.db_path, business_type, app)
            app._demo_worker = worker
            worker.finished_ok.connect(lambda kind: logger.info(f'Demo data status: {kind}'))
            worker.failed.connect(lambda err: logger.warning(f'Demo data generation failed: {err}'))
            worker.start()
    
    login_window.login_successful.connect(on_login_success)
    login_window.show()
    
    logger.info("Application UI ready")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
