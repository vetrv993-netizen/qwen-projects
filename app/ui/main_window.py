"""
Modern main application window with sidebar, header, and content area.
"""
import logging
from typing import Optional
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QStackedWidget, QSizePolicy,
    QStatusBar, QMessageBox, QApplication, QScrollArea,
    QSizePolicy, QGridLayout, QLineEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QComboBox, QDateEdit,
    QDoubleSpinBox, QSpinBox, QTextEdit, QDialog,
    QTabWidget, QCheckBox, QSplitter, QListWidget,
    QListWidgetItem, QFormLayout, QGroupBox, QFileDialog, QTextBrowser,
)
from PySide6.QtCore import Qt, QTimer, QSize, QDate, QUrl
from PySide6.QtGui import QFont, QIcon, QColor, QTextDocument, QAction, QPageLayout, QPageSize
from PySide6.QtPrintSupport import QPrinter, QPrintDialog

from app.database.connection import DatabaseManager
from app.services.auth_service import AuthService
from app.services.backup_service import BackupService
from app.services.sale_service import SaleService
from app.services.purchase_service import PurchaseService
from app.services.notification_service import NotificationService
from app.repositories.audit_repo import AuditRepository
from app.repositories.settings_repo import SettingsRepository
from app.repositories.product_repo import ProductRepository
from app.repositories.customer_repo import CustomerRepository
from app.repositories.supplier_repo import SupplierRepository
from app.repositories.sale_repo import SaleRepository
from app.repositories.purchase_repo import PurchaseRepository
from app.repositories.category_repo import CategoryRepository
from app.repositories.payment_repo import PaymentRepository
from app.repositories.inventory_repo import InventoryRepository
from app.repositories.accounting_repo import AccountingRepository
from app.services.accounting_service import AccountingService
from app.services.reports_service import ReportsService
from app.domain.models import User
from app.config.settings import AppSettings
from app.utils.i18n import t, set_language
from app.ui.styles import COLORS, build_styles, palette, ACCENTS, THEMES


logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window with modern sidebar navigation."""
    
    def __init__(
        self,
        db: DatabaseManager,
        auth_service: AuthService,
        user: User,
        settings: AppSettings,
        business_type: str = 'default',
    ):
        super().__init__()
        
        self.db = db
        self.auth_service = auth_service
        self.user = user
        self.settings = settings
        self.business_type = business_type
        
        # Initialize services
        self.audit_repo = AuditRepository(db)
        self.settings_repo = SettingsRepository(db)
        self.backup_service = BackupService(db, settings.backup_dir)
        self.sale_service = SaleService(db)
        self.purchase_service = PurchaseService(db)
        self.notification_service = NotificationService(db)
        self.product_repo = ProductRepository(db)
        self.customer_repo = CustomerRepository(db)
        self.supplier_repo = SupplierRepository(db)
        self.sale_repo = SaleRepository(db)
        self.purchase_repo = PurchaseRepository(db)
        self.category_repo = CategoryRepository(db)
        self.payment_repo = PaymentRepository(db)
        self.inventory_repo = InventoryRepository(db)
        self.accounting_repo = AccountingRepository(db)
        self.accounting_service = AccountingService(db)
        self.reports_service = ReportsService(db)
        
        # Initialize default settings
        self.settings_repo.initialize_defaults()

        self.theme_mode = self.settings_repo.get_default('theme', 'light')
        self.theme_accent = self.settings_repo.get_default('accent_color', 'indigo')
        COLORS.clear(); COLORS.update(palette(self.theme_mode, self.theme_accent))

        lang = self.settings_repo.get_default('language', 'ar')
        set_language(lang)
        
        self._setup_ui()
        self._setup_status_bar()
        self._setup_timer()
        self._show_page('dashboard')
        
        logger.info(f"Main window initialized for user: {user.username}, business: {business_type}")
    
    def _setup_ui(self):
        business_labels = {
            'default': 'نظام المحاسبة',
            'supermarket': 'سوبرماركت',
            'pharmacy': 'صيدلية',
            'restaurant': 'مطعم',
            'hotel': 'فندق',
        }
        biz_label = business_labels.get(self.business_type, 'نظام المحاسبة')
        
        self.setWindowTitle(f"{biz_label} - {self.user.display_name}")
        self.setMinimumSize(1280, 780)
        self.resize(1500, 900)
        
        self.setStyleSheet(build_styles(self.theme_mode, self.theme_accent))
        
        self._set_window_icon()
        
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self._create_sidebar(main_layout)
        
        # Right side
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        # Header
        self._create_header(right_layout)
        
        # Content area
        self.content_area = QStackedWidget()
        self.content_area.setStyleSheet(f"background-color: {COLORS['background']};")
        
        self._create_pages()
        right_layout.addWidget(self.content_area, 1)
        
        main_layout.addWidget(right_panel, 1)
    
    def _set_window_icon(self):
        import os, sys
        icon_paths = []
        if hasattr(sys, '_MEIPASS'):
            icon_paths.append(os.path.join(sys._MEIPASS, 'assets', 'icon.ico'))
        icon_paths.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assets', 'icon.ico'))
        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
                if not icon.isNull():
                    self.setWindowIcon(icon)
                    return
    
    def _create_sidebar(self, parent_layout):
        sidebar = QFrame()
        sidebar.setFixedWidth(270)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['sidebar']};
                border: none;
            }}
        """)
        
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(2)
        
        # Brand header
        brand = QFrame()
        brand.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1e40af, stop:1 #3b82f6);
                padding: 16px;
            }}
        """)
        brand.setFixedHeight(70)
        brand_layout = QVBoxLayout(brand)
        brand_layout.setContentsMargins(16, 12, 16, 12)
        
        biz_icons = {
            'default': '📊', 'supermarket': '🛒', 'pharmacy': '💊',
            'restaurant': '🍽️', 'hotel': '🏨',
        }
        biz_names = {
            'default': 'نظام المحاسبة', 'supermarket': 'سوبرماركت',
            'pharmacy': 'صيدلية', 'restaurant': 'مطعم', 'hotel': 'فندق',
        }
        
        brand_title = QLabel(f"{biz_icons.get(self.business_type, '📊')}  {biz_names.get(self.business_type, 'نظام المحاسبة')}")
        brand_title.setStyleSheet("color: white; font-size: 12pt; font-weight: 700; background: transparent;")
        brand_layout.addWidget(brand_title)
        
        sidebar_layout.addWidget(brand)
        sidebar_layout.addSpacing(8)
        
        # Navigation
        self.nav_buttons = {}
        nav_items = [
            ('dashboard', '🏠', 'لوحة التحكم'),
            ('pos', '💰', 'نقطة البيع'),
            ('sales', '📋', 'المبيعات'),
            ('purchases', '📦', 'المشتريات'),
            ('inventory', '📦', 'المخزون'),
            ('customers', '👥', 'العملاء'),
            ('suppliers', '🏭', 'المورّدون'),
            ('payments', '💳', 'التحصيلات والدفعات'),
            ('reports', '📊', 'التقارير'),
            ('accounting', '🧾', 'المحاسبة'),
            ('settings', '⚙️', 'الإعدادات'),
        ]
        
        for page_id, icon, label in nav_items:
            btn = QPushButton(f"  {icon}   {label}")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(46)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent; color: #cbd5e1;
                    border: none; text-align: right; padding: 0 20px;
                    font-size: 11pt; font-weight: 600; border-radius: 0;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['sidebar_hover']}; color: white;
                }}
                QPushButton:checked {{
                    background-color: {COLORS['sidebar_active']}; color: white;
                    font-weight: 600; border-right: 3px solid white;
                }}
            """)
            btn.clicked.connect(lambda checked, pid=page_id: self._show_page(pid))
            sidebar_layout.addWidget(btn)
            self.nav_buttons[page_id] = btn
        
        sidebar_layout.addStretch()
        
        # User info at bottom
        user_frame = QFrame()
        user_frame.setStyleSheet(f"""
            QFrame {{
                background-color: #0f172a;
                border-top: 1px solid #334155;
            }}
        """)
        user_frame.setFixedHeight(60)
        user_layout = QHBoxLayout(user_frame)
        user_layout.setContentsMargins(14, 8, 14, 8)
        
        user_info = QVBoxLayout()
        user_name = QLabel(self.user.display_name)
        user_name.setStyleSheet("color: white; font-weight: 600; font-size: 9pt; background: transparent;")
        user_info.addWidget(user_name)
        
        from app.security.permissions import get_role_label, Role
        role_label = QLabel(get_role_label(Role(self.user.role), 'ar'))
        role_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 8pt; background: transparent;")
        user_info.addWidget(role_label)
        
        user_layout.addLayout(user_info)
        user_layout.addStretch()
        
        logout_btn = QPushButton("🚪")
        logout_btn.setFixedSize(36, 36)
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.setToolTip("تسجيل الخروج")
        logout_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent; color: #94a3b8;
                border: none; border-radius: 8px; font-size: 14pt;
            }}
            QPushButton:hover {{ background-color: #ef4444; color: white; }}
        """)
        logout_btn.clicked.connect(self._on_logout)
        user_layout.addWidget(logout_btn)
        
        sidebar_layout.addWidget(user_frame)
        parent_layout.addWidget(sidebar)
    
    def _create_header(self, parent_layout):
        header = QFrame()
        header.setFixedHeight(64)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        
        self.page_title = QLabel("لوحة التحكم")
        self.page_title.setStyleSheet(f"font-size: 14pt; font-weight: 700; color: {COLORS['text']};")
        header_layout.addWidget(self.page_title)
        
        header_layout.addStretch()
        
        # Search
        self.global_search = QLineEdit()
        self.global_search.setPlaceholderText("🔍 بحث سريع...")
        self.global_search.setFixedWidth(250)
        self.global_search.setStyleSheet(f"""
            QLineEdit {{
                padding: 8px 14px; border: 1px solid {COLORS['border']};
                border-radius: 8px; font-size: 9pt; background: {COLORS['background']};
            }}
            QLineEdit:focus {{ border-color: {COLORS['primary']}; }}
        """)
        header_layout.addWidget(self.global_search)
        
        header_layout.addSpacing(12)
        
        # Notifications
        self.notif_btn = QPushButton("🔔")
        self.notif_btn.setFixedSize(40, 40)
        self.notif_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.notif_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['background']}; border: 1px solid {COLORS['border']};
                border-radius: 10px; font-size: 14pt;
            }}
            QPushButton:hover {{ background: {COLORS['border']}; }}
        """)
        header_layout.addWidget(self.notif_btn)
        
        header_layout.addSpacing(8)
        
        # Date/time
        self.datetime_label = QLabel()
        self.datetime_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 9pt;")
        header_layout.addWidget(self.datetime_label)
        parent_layout.addWidget(header)
    
    def _create_pages(self):
        """Create all content pages."""
        self.pages = {}
        
        self.pages['dashboard'] = self._create_dashboard_page()
        self.pages['pos'] = self._create_pos_page()
        self.pages['sales'] = self._create_sales_page()
        self.pages['purchases'] = self._create_purchases_page()
        self.pages['inventory'] = self._create_inventory_page()
        self.pages['customers'] = self._create_customers_page()
        self.pages['suppliers'] = self._create_suppliers_page()
        self.pages['payments'] = self._create_payments_page()
        self.pages['reports'] = self._create_reports_page()
        self.pages['accounting'] = self._create_accounting_page()
        self.pages['settings'] = self._create_settings_page()
        
        for page in self.pages.values():
            self.content_area.addWidget(page)
    
    def _make_card(self) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['surface']}; color: {COLORS['text']}; border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        return card
    
    def _make_stat_card(self, title: str, value: str, icon: str, color: str) -> QFrame:
        card = self._make_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)
        
        top = QHBoxLayout()
        icon_l = QLabel(icon)
        icon_l.setStyleSheet(f"font-size: 20pt; background: {color}22; border-radius: 10px; padding: 8px;")
        icon_l.setFixedSize(48, 48)
        icon_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top.addWidget(icon_l)
        top.addStretch()
        layout.addLayout(top)
        
        val_l = QLabel(value)
        val_l.setStyleSheet(f"font-size: 18pt; font-weight: 800; color: {COLORS['text']};")
        layout.addWidget(val_l)
        
        title_l = QLabel(title)
        title_l.setStyleSheet(f"font-size: 9pt; color: {COLORS['text_secondary']};")
        layout.addWidget(title_l)
        
        card._value_label = val_l
        return card
    
    def _create_dashboard_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)
        
        # Welcome
        welcome = QLabel(f"مرحباً، {self.user.display_name}")
        welcome.setStyleSheet(f"font-size: 14pt; font-weight: 600; color: {COLORS['text']};")
        layout.addWidget(welcome)
        
        # Stats grid
        stats_grid = QGridLayout()
        stats_grid.setSpacing(14)
        
        today_sales = self.sale_repo.get_today_total()
        today_purchases = self.purchase_repo.get_today_total()
        customer_debts = self.customer_repo.get_total_receivables()
        supplier_dues = self.supplier_repo.get_total_payables()
        stock_value = self.product_repo.total_stock_value()
        product_count = self.product_repo.count()
        
        stats = [
            ("مبيعات اليوم", f"{today_sales:,.0f}", "💰", COLORS['primary']),
            ("مشتريات اليوم", f"{today_purchases:,.0f}", "📦", COLORS['success']),
            ("ديون العملاء", f"{customer_debts:,.0f}", "👥", COLORS['warning']),
            ("مستحقات المورّدين", f"{supplier_dues:,.0f}", "🏭", COLORS['danger']),
            ("قيمة المخزون", f"{stock_value:,.0f}", "📊", COLORS['info']),
            ("عدد المنتجات", f"{product_count}", "🏷️", '#8b5cf6'),
        ]
        
        for i, (title, value, icon, color) in enumerate(stats):
            card = self._make_stat_card(title, value, icon, color)
            stats_grid.addWidget(card, i // 3, i % 3)
        
        layout.addLayout(stats_grid)
        
        # Quick actions + recent
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(14)
        
        # Quick actions
        actions_card = self._make_card()
        actions_layout = QVBoxLayout(actions_card)
        actions_layout.setContentsMargins(18, 16, 18, 16)
        
        actions_title = QLabel("⚡ إجراءات سريعة")
        actions_title.setStyleSheet(f"font-size: 11pt; font-weight: 700; color: {COLORS['text']};")
        actions_layout.addWidget(actions_title)
        
        actions_grid = QGridLayout()
        actions_grid.setHorizontalSpacing(10)
        actions_grid.setVerticalSpacing(10)
        
        quick_actions = [
            ("💰", "بيعة جديدة", 'pos'),
            ("📦", "شراء جديد", 'purchases'),
            ("🏷️", "إضافة منتج", 'inventory'),
            ("💵", "تحصيل مبلغ", 'customers'),
            ("👤", "عميل جديد", 'customers'),
            ("🏭", "مورّد جديد", 'suppliers'),
        ]
        
        action_roles = ["primary", "success", "warning", "info", "secondary", "danger"]
        for i, (icon, label, page_id) in enumerate(quick_actions):
            btn = QPushButton(f"{icon}  {label}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(46)
            btn.setStyleSheet(self._semantic_button_style(action_roles[i], compact=True))
            btn.clicked.connect(lambda checked, pid=page_id: self._show_page(pid))
            actions_grid.addWidget(btn, i // 2, i % 2)
        
        actions_layout.addLayout(actions_grid)
        actions_layout.addStretch()
        bottom_layout.addWidget(actions_card, 1)
        
        # Recent sales
        recent_card = self._make_card()
        recent_layout = QVBoxLayout(recent_card)
        recent_layout.setContentsMargins(18, 16, 18, 16)
        
        recent_title = QLabel("📋 آخر الفواتير")
        recent_title.setStyleSheet(f"font-size: 11pt; font-weight: 700; color: {COLORS['text']};")
        recent_layout.addWidget(recent_title)
        
        recent_table = QTableWidget()
        recent_table.setColumnCount(4)
        recent_table.setHorizontalHeaderLabels(["رقم الفاتورة", "المبلغ", "الحالة", "التاريخ"])
        recent_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        recent_table.setAlternatingRowColors(True)
        recent_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        recent_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        recent_table.verticalHeader().setVisible(False)
        recent_table.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {COLORS['border']}; border-radius: 8px;
                gridline-color: {COLORS['border_light']};
                font-size: 9pt;
            }}
            QHeaderView::section {{
                background: {COLORS['background']}; padding: 8px;
                border: none; border-bottom: 2px solid {COLORS['border']};
                font-weight: 600; color: {COLORS['text_secondary']};
            }}
        """)
        
        recent_sales = self.sale_repo.get_all(limit=8)
        recent_table.setRowCount(len(recent_sales))
        
        for row, sale in enumerate(recent_sales):
            recent_table.setItem(row, 0, QTableWidgetItem(sale['invoice_number']))
            recent_table.setItem(row, 1, QTableWidgetItem(f"{sale['total_amount']:,.0f}"))
            
            status_item = QTableWidgetItem(sale['payment_status'])
            if sale['payment_status'] == 'paid':
                status_item.setForeground(QColor(COLORS['success']))
            elif sale['payment_status'] == 'partial':
                status_item.setForeground(QColor(COLORS['warning']))
            else:
                status_item.setForeground(QColor(COLORS['danger']))
            recent_table.setItem(row, 2, status_item)
            
            recent_table.setItem(row, 3, QTableWidgetItem(sale['sale_date'][:10]))
        
        recent_layout.addWidget(recent_table)
        bottom_layout.addWidget(recent_card, 2)
        
        layout.addLayout(bottom_layout, 1)
        return page
    
    def _create_pos_page(self) -> QWidget:
        """Create POS page with product search, cart, and payment."""
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Left: Products
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        
        # Search
        search_card = self._make_card()
        search_layout = QVBoxLayout(search_card)
        search_layout.setContentsMargins(12, 10, 12, 10)
        
        self.pos_search = QLineEdit()
        self.pos_search.setPlaceholderText("🔍 بحث بالاسم أو الباركود...")
        self.pos_search.setStyleSheet(f"""
            QLineEdit {{
                padding: 12px 16px; border: 2px solid {COLORS['border']};
                border-radius: 10px; font-size: 11pt; background: {COLORS['surface']};
            }}
            QLineEdit:focus {{ border-color: {COLORS['primary']}; }}
        """)
        self.pos_search.textChanged.connect(self._pos_search_products)
        search_layout.addWidget(self.pos_search)
        left_layout.addWidget(search_card)
        
        # Categories — horizontally scrollable so all category buttons remain visible
        cat_card = self._make_card()
        cat_outer = QHBoxLayout(cat_card)
        cat_outer.setContentsMargins(8, 6, 8, 6)
        cat_scroll = QScrollArea()
        cat_scroll.setWidgetResizable(True)
        cat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        cat_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        cat_scroll.setFrameShape(QFrame.Shape.NoFrame)
        cat_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        cat_widget = QWidget()
        cat_layout = QHBoxLayout(cat_widget)
        cat_layout.setContentsMargins(2, 2, 2, 2)
        cat_layout.setSpacing(8)

        all_btn = QPushButton("الكل")
        all_btn.setCheckable(True)
        all_btn.setChecked(True)
        all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        all_btn.setMinimumWidth(82)
        all_btn.setStyleSheet(self._cat_btn_style(True))
        all_btn.clicked.connect(lambda: self._pos_filter_category(None, all_btn))
        cat_layout.addWidget(all_btn)

        categories = self.category_repo.get_all()
        self._pos_cat_buttons = [all_btn]
        for cat in categories:
            btn = QPushButton(cat['name_ar'])
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumWidth(92)
            btn.setStyleSheet(self._cat_btn_style(False))
            btn.clicked.connect(lambda checked, c=cat['id'], b=btn: self._pos_filter_category(c, b))
            cat_layout.addWidget(btn)
            self._pos_cat_buttons.append(btn)
        cat_layout.addStretch()
        cat_scroll.setWidget(cat_widget)
        cat_outer.addWidget(cat_scroll)
        left_layout.addWidget(cat_card)
        
        # Products grid
        self.pos_products_scroll = QScrollArea()
        self.pos_products_scroll.setWidgetResizable(True)
        self.pos_products_scroll.setStyleSheet(f"QScrollArea {{ border: none; background: {COLORS['background']}; }}")
        
        self.pos_products_widget = QWidget()
        self.pos_products_layout = QGridLayout(self.pos_products_widget)
        self.pos_products_layout.setSpacing(10)
        self.pos_products_layout.setContentsMargins(0, 0, 0, 0)
        
        self.pos_products_scroll.setWidget(self.pos_products_widget)
        left_layout.addWidget(self.pos_products_scroll, 1)
        
        layout.addWidget(left_panel, 3)
        
        # Right: Cart + Payment
        right_panel = QWidget()
        right_panel.setFixedWidth(380)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)
        
        # Cart header
        cart_header = self._make_card()
        ch_layout = QHBoxLayout(cart_header)
        ch_layout.setContentsMargins(14, 10, 14, 10)
        
        cart_title = QLabel("🛒 الفاتورة الحالية")
        cart_title.setStyleSheet(f"font-size: 11pt; font-weight: 700; color: {COLORS['text']};")
        ch_layout.addWidget(cart_title)
        ch_layout.addStretch()
        
        clear_btn = QPushButton("🗑️")
        clear_btn.setFixedSize(36, 36)
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setToolTip("مسح الفاتورة")
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['danger_light']}; color: {COLORS['danger']};
                border: none; border-radius: 8px; font-size: 14pt;
            }}
            QPushButton:hover {{ background: {COLORS['danger']}; color: white; }}
        """)
        clear_btn.clicked.connect(self._pos_clear_cart)
        ch_layout.addWidget(clear_btn)
        
        right_layout.addWidget(cart_header)
        
        # Cart items
        self.pos_cart_table = QTableWidget()
        self.pos_cart_table.setColumnCount(4)
        self.pos_cart_table.setHorizontalHeaderLabels(["المنتج", "السعر", "الكمية", "الإجمالي"])
        self.pos_cart_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.pos_cart_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.pos_cart_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.pos_cart_table.verticalHeader().setVisible(False)
        self.pos_cart_table.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {COLORS['border']}; border-radius: 10px;
                gridline-color: {COLORS['border_light']}; font-size: 9pt;
            }}
            QHeaderView::section {{
                background: {COLORS['table_alt']}; padding: 8px;
                border: none; font-weight: 600;
                color: {COLORS['text_secondary']}; font-size: 8pt;
            }}
        """)
        right_layout.addWidget(self.pos_cart_table, 1)
        
        # Cart data
        self._cart_items = []
        
        # Totals
        totals_card = self._make_card()
        totals_layout = QVBoxLayout(totals_card)
        totals_layout.setContentsMargins(16, 12, 16, 12)
        totals_layout.setSpacing(8)
        
        self.pos_subtotal_label = self._totals_row("المجموع الفرعي", "0", parent_layout=totals_layout)
        self.pos_discount_label = self._totals_row("الخصم", "0", parent_layout=totals_layout)
        self.pos_tax_label = self._totals_row("الضريبة", "0", parent_layout=totals_layout)
        
        sep = QFrame()
        sep.setFixedHeight(2)
        sep.setStyleSheet(f"background: {COLORS['border']};")
        totals_layout.addWidget(sep)
        
        self.pos_total_label = self._totals_row("الإجمالي", "0", big=True, parent_layout=totals_layout)
        
        right_layout.addWidget(totals_card)

        # Advanced invoice controls: discount + tax
        options_card = self._make_card()
        options_layout = QGridLayout(options_card)
        options_layout.setContentsMargins(12, 10, 12, 10)
        options_layout.addWidget(QLabel('🏷️ الخصم'), 0, 0)
        self.pos_discount_input = QDoubleSpinBox(); self.pos_discount_input.setRange(0, 1e9); self.pos_discount_input.setDecimals(2); self.pos_discount_input.setSuffix(' ﷼')
        options_layout.addWidget(self.pos_discount_input, 0, 1)
        options_layout.addWidget(QLabel('🧾 الضريبة %'), 1, 0)
        self.pos_tax_input = QDoubleSpinBox(); self.pos_tax_input.setRange(0, 100); self.pos_tax_input.setDecimals(2); self.pos_tax_input.setValue(float(self.settings_repo.get_default('tax_rate', '15')))
        options_layout.addWidget(self.pos_tax_input, 1, 1)
        self.pos_discount_input.valueChanged.connect(self._pos_update_cart_display)
        self.pos_tax_input.valueChanged.connect(self._pos_update_cart_display)
        right_layout.addWidget(options_card)

        # Payment
        pay_card = self._make_card()
        pay_layout = QVBoxLayout(pay_card)
        pay_layout.setContentsMargins(14, 12, 14, 12)
        pay_layout.setSpacing(8)
        
        pay_label = QLabel("💳 الدفع")
        pay_label.setStyleSheet(f"font-size: 10pt; font-weight: 700; color: {COLORS['text']};")
        pay_layout.addWidget(pay_label)
        
        self.pos_paid_input = QDoubleSpinBox()
        self.pos_paid_input.setRange(0, 999999999)
        self.pos_paid_input.setDecimals(0)
        self.pos_paid_input.setPrefix("﷼ ")
        self.pos_paid_input.setStyleSheet(f"""
            QDoubleSpinBox {{
                padding: 10px; border: 2px solid {COLORS['border']};
                border-radius: 8px; font-size: 12pt; font-weight: 700;
            }}
            QDoubleSpinBox:focus {{ border-color: {COLORS['primary']}; }}
        """)
        pay_layout.addWidget(self.pos_paid_input)
        
        self.pos_checkout_btn = QPushButton("✅ إتمام البيع")
        self.pos_checkout_btn.setFixedHeight(50)
        self.pos_checkout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pos_checkout_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['success']}; color: white;
                border: none; border-radius: 12px;
                font-size: 13pt; font-weight: 800;
            }}
            QPushButton:hover {{ background: {COLORS['success_dark']}; }}
            QPushButton:disabled {{ background: {COLORS['text_muted']}; }}
        """)
        self.pos_checkout_btn.clicked.connect(self._pos_checkout)
        pay_layout.addWidget(self.pos_checkout_btn)
        
        right_layout.addWidget(pay_card)
        layout.addWidget(right_panel)
        
        # Load products
        self._pos_load_products()
        
        return page
    
    def _cat_btn_style(self, active: bool) -> str:
        if active:
            return f"""
                QPushButton {{
                    background: {COLORS['primary']}; color: white;
                    border: none; border-radius: 8px; padding: 8px 16px;
                    font-size: 9pt; font-weight: 600;
                }}
            """
        return f"""
            QPushButton {{
                background: {COLORS['background']}; color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border']}; border-radius: 8px;
                padding: 8px 16px; font-size: 9pt;
            }}
            QPushButton:hover {{ background: {COLORS['border']}; }}
        """
    
    def _totals_row(self, label: str, value: str, big: bool = False, parent_layout=None) -> tuple:
        row = QHBoxLayout()
        l = QLabel(label)
        l.setStyleSheet(f"font-size: {'11pt' if big else '9pt'}; color: {COLORS['text_secondary']};")
        row.addWidget(l)
        row.addStretch()
        v = QLabel(value)
        v.setStyleSheet(f"font-size: {'14pt' if big else '10pt'}; font-weight: {'800' if big else '600'}; color: {COLORS['text']};")
        row.addWidget(v)

        if parent_layout is not None:
            parent_layout.addLayout(row)

        return l, v
    
    def _pos_load_products(self, query: str = '', category_id: int = None):
        """Load products into POS grid."""
        # Clear existing
        while self.pos_products_layout.count():
            item = self.pos_products_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        products = self.product_repo.search(query) if query else self.product_repo.get_all(category_id=category_id)
        
        for i, product in enumerate(products[:60]):
            card = QFrame()
            card.setCursor(Qt.CursorShape.PointingHandCursor)
            card.setStyleSheet(f"""
                QFrame {{
                    background: {COLORS['surface']}; border: 1px solid {COLORS['border']};
                    border-radius: 10px; padding: 8px;
                }}
                QFrame:hover {{
                    border-color: {COLORS['primary']}; background: {COLORS['primary_light']};
                }}
            """)
            card.setMinimumHeight(118)
            
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(10, 8, 10, 8)
            card_layout.setSpacing(4)
            
            name = QLabel(product['name_ar'])
            name.setStyleSheet(f"font-family: 'Segoe UI', 'Tahoma', sans-serif; font-size: 10pt; font-weight: 700; color: {COLORS['text']}; background: transparent; border: none;")
            name.setWordWrap(True)
            card_layout.addWidget(name)
            
            card_layout.addStretch()
            
            price = QLabel(f"﷼ {product['selling_price']:,.0f}")
            price.setStyleSheet(f"font-family: 'Segoe UI', 'Tahoma', sans-serif; font-size: 11.5pt; font-weight: 800; color: {COLORS['primary']}; background: transparent; border: none;")
            card_layout.addWidget(price)
            
            stock = QLabel(f"المخزون: {product['stock_quantity']}")
            stock.setStyleSheet(f"font-family: 'Segoe UI', 'Tahoma', sans-serif; font-size: 8.5pt; color: {COLORS['text_secondary']}; background: transparent; border: none;")
            card_layout.addWidget(stock)
            
            card.mousePressEvent = lambda e, p=product: self._pos_add_to_cart(p)
            self.pos_products_layout.addWidget(card, i // 4, i % 4)
    
    def _pos_search_products(self, query: str):
        self._pos_load_products(query)
    
    def _pos_filter_category(self, category_id: int, btn: QPushButton):
        for b in self._pos_cat_buttons:
            b.setChecked(b == btn)
            b.setStyleSheet(self._cat_btn_style(b == btn))
        self._pos_load_products(category_id=category_id)
    
    def _pos_add_to_cart(self, product: dict):
        """Add product to cart."""
        # Check if already in cart
        for item in self._cart_items:
            if item['product_id'] == product['id']:
                item['quantity'] += 1
                self._pos_update_cart_display()
                return
        
        self._cart_items.append({
            'product_id': product['id'],
            'name_ar': product['name_ar'],
            'unit_price': product['selling_price'],
            'quantity': 1,
        })
        self._pos_update_cart_display()
    
    def _pos_update_cart_display(self):
        """Update cart table and totals."""
        self.pos_cart_table.setRowCount(len(self._cart_items))
        
        subtotal = 0
        for row, item in enumerate(self._cart_items):
            total = item['unit_price'] * item['quantity']
            subtotal += total
            
            self.pos_cart_table.setItem(row, 0, QTableWidgetItem(item['name_ar']))
            self.pos_cart_table.setItem(row, 1, QTableWidgetItem(f"{item['unit_price']:,.0f}"))
            self.pos_cart_table.setItem(row, 2, QTableWidgetItem(str(item['quantity'])))
            self.pos_cart_table.setItem(row, 3, QTableWidgetItem(f"{total:,.0f}"))
        
        discount = min(self.pos_discount_input.value() if hasattr(self, 'pos_discount_input') else 0.0, subtotal)
        tax_rate = self.pos_tax_input.value() if hasattr(self, 'pos_tax_input') else float(self.settings_repo.get_default('tax_rate', '15'))
        taxable = max(0.0, subtotal - discount)
        tax = taxable * (tax_rate / 100)
        grand_total = taxable + tax
        
        self.pos_subtotal_label[1].setText(f"﷼ {subtotal:,.2f}")
        self.pos_discount_label[1].setText(f"﷼ {discount:,.2f}")
        self.pos_tax_label[1].setText(f"﷼ {tax:,.0f}")
        self.pos_total_label[1].setText(f"﷼ {grand_total:,.0f}")
        
        self.pos_paid_input.setValue(grand_total)
    
    def _pos_clear_cart(self):
        self._cart_items.clear()
        self._pos_update_cart_display()
    
    def _pos_checkout(self):
        """Complete the sale."""
        if not self._cart_items:
            QMessageBox.warning(self, "تنبيه", "السلة فارغة")
            return
        
        try:
            tax_rate = self.pos_tax_input.value() if hasattr(self, 'pos_tax_input') else float(self.settings_repo.get_default('tax_rate', '15'))
            discount_amount = self.pos_discount_input.value() if hasattr(self, 'pos_discount_input') else 0.0
            paid = self.pos_paid_input.value()
            
            result = self.sale_service.create_sale(
                items=[{
                    'product_id': item['product_id'],
                    'quantity': item['quantity'],
                    'unit_price': item['unit_price'],
                    'discount': 0,
                } for item in self._cart_items],
                discount_amount=discount_amount,
                tax_rate=tax_rate,
                paid_amount=paid,
                payment_method='cash',
                created_by=self.user.id,
            )
            
            QMessageBox.information(
                self, "تم بنجاح",
                f"✅ تم إنشاء الفاتورة: {result['invoice_number']}\n"
                f"الإجمالي: ﷼ {result['total_amount']:,.0f}\n"
                f"المدفوع: ﷼ {result['paid_amount']:,.0f}\n"
                f"المتبقي: ﷼ {result['remaining']:,.0f}"
            )
            
            self._cart_items.clear()
            self._pos_update_cart_display()
            self._pos_load_products()
            self.pos_search.clear()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))
    
    def _semantic_button_style(self, role="secondary", compact=False):
        roles = {
            "primary": (COLORS['primary'], COLORS['primary_dark'], "white"),
            "secondary": (COLORS['surface'], COLORS['primary'], COLORS['text']),
            "success": (COLORS['success'], "#059669", "white"),
            "danger": (COLORS['danger'], "#dc2626", "white"),
            "warning": (COLORS['warning'], "#d97706", "white"),
            "info": (COLORS['info'], "#0284c7", "white"),
        }
        bg, hover, fg = roles.get(role, roles['secondary'])
        if compact:
            return f"""
                QPushButton {{ background:{bg}; color:{fg}; border:1px solid {bg}; border-radius:7px; padding:3px 7px; min-height:26px; min-width:62px; max-height:30px; font-size:9pt; font-weight:700; }}
                QPushButton:hover {{ background:{hover}; color:white; border-color:{hover}; }}
                QPushButton:pressed {{ background:{hover}; color:white; }}
                QPushButton:disabled {{ background:{COLORS['text_muted']}; color:white; border-color:{COLORS['text_muted']}; }}
            """
        return f"""
            QPushButton {{ background:{bg}; color:{fg}; border:1px solid {bg}; border-radius:9px; padding:8px 14px; min-height:34px; font-weight:700; }}
            QPushButton:hover {{ background:{hover}; color:white; border-color:{hover}; }}
            QPushButton:pressed {{ background:{hover}; color:white; }}
            QPushButton:disabled {{ background:{COLORS['text_muted']}; color:white; border-color:{COLORS['text_muted']}; }}
        """

    def _compact_action_button(self, text, role, callback, tooltip=None, width=68):
        b = QPushButton(text)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setFixedSize(width, 28)
        b.setMinimumSize(width, 28)
        b.setStyleSheet(self._semantic_button_style(role, compact=True))
        if tooltip:
            b.setToolTip(tooltip)
        b.clicked.connect(callback)
        return b

    def _action_icon_button(self, icon, role, callback, tooltip):
        b = QPushButton(icon)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setFixedSize(34, 30)
        b.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        b.setToolTip(tooltip)
        b.setAccessibleName(tooltip)
        b.setStatusTip(tooltip)
        b.setStyleSheet(self._semantic_button_style(role, compact=True) + "\n"
                        "QPushButton { padding:0px; min-width:34px; max-width:34px; font-size:11pt; font-weight:800; }\n")
        b.clicked.connect(callback)
        return b

    def _action_row(self, buttons):
        w = QWidget()
        l = QHBoxLayout(w)
        l.setContentsMargins(6, 3, 6, 3)
        l.setSpacing(7)
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        for b in buttons:
            l.addWidget(b)
        w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        return w

    def _page_toolbar(self, title: str, search_placeholder: str, add_text: str, add_slot):
        bar = QHBoxLayout()
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"font-size: 15pt; font-weight: 800; color: {COLORS['text']};")
        bar.addWidget(title_lbl)
        bar.addStretch()
        search = QLineEdit()
        search.setPlaceholderText(search_placeholder)
        search.setClearButtonEnabled(True)
        search.setFixedWidth(300)
        bar.addWidget(search)
        add_btn = QPushButton(add_text)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet(f"QPushButton {{ background:{COLORS['primary']}; color:white; border-radius:8px; padding:6px 14px; font-weight:700; }} QPushButton:hover{{background:{COLORS['primary_dark']};}}")
        add_btn.clicked.connect(add_slot)
        bar.addWidget(add_btn)
        return bar, search

    def _table(self, headers, widths=None):
        table=QTableWidget()
        table.setColumnCount(len(headers)); table.setHorizontalHeaderLabels(headers)
        if widths:
            for i,w in enumerate(widths): table.setColumnWidth(i,w)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setAlternatingRowColors(True); table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows); table.verticalHeader().setVisible(False)
        table.setStyleSheet(f"""QTableWidget {{ border:1px solid {COLORS['border']}; border-radius:10px; gridline-color:{COLORS['border_light']}; }}
        QHeaderView::section {{ background:{COLORS['table_alt']}; color:{COLORS['text']}; padding:10px; border:none; border-bottom:2px solid {COLORS['border']}; font-weight:700; }}""")
        return table

    def _action_buttons(self, table, row_id, allow_delete=True, detail_slot=None, edit_slot=None, extra_slot=None):
        w=QWidget(); l=QHBoxLayout(w); l.setContentsMargins(4,2,4,2); l.setSpacing(5); w.setMinimumWidth(270)
        if detail_slot:
            b=QPushButton('تفاصيل'); b.setStyleSheet(self._semantic_button_style('info', compact=True)); b.clicked.connect(lambda: detail_slot(row_id)); l.addWidget(b)
        if edit_slot:
            b=QPushButton('تعديل'); b.setStyleSheet(self._semantic_button_style('primary', compact=True)); b.clicked.connect(lambda: edit_slot(row_id)); l.addWidget(b)
        if extra_slot:
            b=QPushButton('إجراء'); b.setStyleSheet(self._semantic_button_style('warning', compact=True)); b.clicked.connect(lambda: extra_slot(row_id)); l.addWidget(b)
        if allow_delete:
            b=QPushButton('حذف'); b.setStyleSheet(self._semantic_button_style('danger', compact=True)); b.clicked.connect(lambda: self._soft_delete_record(row_id)); l.addWidget(b)
        return w

    def _soft_delete_record(self, entity_id):
        QMessageBox.information(self, 'حذف', 'الحذف العام متاح للسجلات الرئيسية من داخل شاشتها، أما الفواتير فلا تُحذف محاسبياً بل تُلغى للحفاظ على سلامة القيود والمخزون.')

    def _create_sales_page(self) -> QWidget:
        page=QWidget(); layout=QVBoxLayout(page); layout.setContentsMargins(24,20,24,20); layout.setSpacing(12)
        toolbar, search=self._page_toolbar('📋 المبيعات','بحث برقم الفاتورة أو العميل…','➕ فاتورة بيع جديدة',lambda:self._show_page('pos'))
        layout.addLayout(toolbar)
        table=self._table(['رقم الفاتورة','العميل','المبلغ','المدفوع','المتبقي','الحالة','التاريخ','الإجراءات'])
        table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(7, 176)
        layout.addWidget(table,1)
        self.sales_table=table
        self.sales_search=search
        search.textChanged.connect(lambda q:self._refresh_sales(q))
        table.cellDoubleClicked.connect(lambda r,c:self._show_sale_details(table.item(r,0).data(Qt.ItemDataRole.UserRole)))
        self._refresh_sales()
        return page

    def _refresh_sales(self, query=''):
        if not hasattr(self,'sales_table'): return
        sales=self.sale_repo.get_all(limit=500)
        q=(query or '').strip().lower()
        if q: sales=[x for x in sales if q in str(x.get('invoice_number','')).lower() or q in str(x.get('customer_name_ar') or '').lower()]
        t=self.sales_table; t.setRowCount(len(sales))
        for r,x in enumerate(sales):
            vals=[x['invoice_number'], x.get('customer_name_ar') or 'نقدي', f"﷼ {x['total_amount']:,.0f}", f"﷼ {x['paid_amount']:,.0f}", f"﷼ {x['remaining_amount']:,.0f}", {'paid':'مدفوع','partial':'جزئي','unpaid':'غير مدفوع'}.get(x['payment_status'],x['payment_status']), x['sale_date'][:10]]
            for c,v in enumerate(vals): t.setItem(r,c,QTableWidgetItem(str(v)))
            t.item(r,0).setData(Qt.ItemDataRole.UserRole,x['id'])
            sid = x['id']
            ab = self._action_row([
                self._action_icon_button('👁', 'info', lambda _, sid=sid: self._preview_sale(sid), 'معاينة الفاتورة'),
                self._action_icon_button('↔', 'primary', lambda _, sid=sid: self._show_sale_details(sid), 'تفاصيل الفاتورة'),
                self._action_icon_button('↩', 'warning', lambda _, sid=sid: self._return_sale(sid), 'إرجاع كامل الفاتورة'),
                self._action_icon_button('✕', 'danger', lambda _, sid=sid: self._cancel_sale(sid), 'إلغاء الفاتورة'),
            ])
            t.setCellWidget(r,7,ab)

    def _show_sale_details(self, sale_id):
        data=self.sale_service.get_sale_with_items(int(sale_id))
        if not data: return
        lines=[f"رقم الفاتورة: {data['invoice_number']}",f"التاريخ: {data['sale_date']}",f"العميل: {data.get('customer_name_ar') or 'نقدي'}",'']
        for i in data.get('items',[]): lines.append(f"{i['name_ar']} × {i['quantity']} = ﷼ {i['total_price']:,.0f}")
        lines += ['',f"الإجمالي: ﷼ {data['total_amount']:,.0f}",f"المدفوع: ﷼ {data['paid_amount']:,.0f}",f"المتبقي: ﷼ {data['remaining_amount']:,.0f}"]
        QMessageBox.information(self,'تفاصيل الفاتورة','\n'.join(lines))

    def _return_sale(self, sale_id):
        sale=self.sale_repo.get_by_id(sale_id)
        if not sale or sale.get('status') != 'completed':
            QMessageBox.warning(self,'المرتجع','لا يمكن إرجاع هذه الفاتورة في حالتها الحالية.')
            return
        if QMessageBox.question(self,'مرتجع كامل','سيتم إعادة كامل كميات الفاتورة للمخزون وعكس الرصيد والقيد المحاسبي. متابعة؟') != QMessageBox.StandardButton.Yes:
            return
        try:
            with self.db.transaction():
                items=self.sale_repo.get_items(sale_id)
                for i in items:
                    self.product_repo.update_stock(i['product_id'], i['quantity'])
                    # Return quantities to the exact lots consumed by the sale when lot tracking exists.
                    lot_rows = self.db.fetch_all(
                        "SELECT lot_id, quantity FROM sale_item_lots WHERE sale_item_id=?", (i['id'],)
                    )
                    for lr in lot_rows:
                        self.db.execute(
                            "UPDATE inventory_lots SET current_quantity=current_quantity+?, updated_at=? WHERE id=?",
                            (lr['quantity'], datetime.now().isoformat(), lr['lot_id'])
                        )
                    self.inventory_repo.record_movement(product_id=i['product_id'], movement_type='in', quantity=i['quantity'], reference_type='sale_return', reference_id=sale_id, created_by=self.user.id)
                if sale.get('customer_id') and sale.get('remaining_amount',0)>0:
                    self.customer_repo.update_balance(sale['customer_id'], -sale['remaining_amount'])
                self.accounting_service.reverse_sale(sale_id, self.user.id)
                self.sale_repo.update(sale_id, status='returned')
            self._refresh_sales(self.sales_search.text())
            QMessageBox.information(self,'تم المرتجع','تم تنفيذ المرتجع الكامل وإعادة المخزون وعكس القيد المحاسبي.')
        except Exception as e:
            QMessageBox.critical(self,'خطأ في المرتجع',str(e))

    def _cancel_sale(self, sale_id):
        sale=self.sale_repo.get_by_id(sale_id)
        if not sale or sale['status']!='completed': return
        if QMessageBox.question(self,'إلغاء الفاتورة','سيتم عكس حركة المخزون والرصد على العميل. متابعة؟')!=QMessageBox.StandardButton.Yes:return
        with self.db.transaction():
            items=self.sale_repo.get_items(sale_id)
            for i in items:
                self.product_repo.update_stock(i['product_id'], i['quantity'])
                lot_rows = self.db.fetch_all("SELECT lot_id, quantity FROM sale_item_lots WHERE sale_item_id=?", (i['id'],))
                for lr in lot_rows:
                    self.db.execute("UPDATE inventory_lots SET current_quantity=current_quantity+?, updated_at=? WHERE id=?", (lr['quantity'], datetime.now().isoformat(), lr['lot_id']))
                self.inventory_repo.record_movement(product_id=i['product_id'],movement_type='in',quantity=i['quantity'],reference_type='sale_cancel',reference_id=sale_id,created_by=self.user.id)
            if sale.get('customer_id') and sale.get('remaining_amount',0)>0:self.customer_repo.update_balance(sale['customer_id'],-sale['remaining_amount'])
            self.accounting_service.reverse_sale(sale_id, self.user.id)
            self.sale_repo.update(sale_id,status='cancelled')
        self._refresh_sales(self.sales_search.text())

    def _print_sale(self, sale_id):
        self._preview_sale(sale_id, auto_print=True)

    def _preview_sale(self, sale_id, auto_print=False):
        data=self.sale_service.get_sale_with_items(int(sale_id))
        if data:
            self._show_invoice_preview(self._sale_html(data), f"معاينة فاتورة البيع {data['invoice_number']}", auto_print=auto_print)

    def _sale_html(self,d):
        org = self.settings_repo.get_default('org_name_ar', self.settings_repo.get_default('org_name', 'المنشأة'))
        currency = self.settings_repo.get_default('currency_symbol', 'ر.س')
        items=''.join(f"<tr><td>{i['name_ar']}</td><td class='num'>{i['quantity']:,.2f}</td><td class='num'>{i['unit_price']:,.2f}</td><td class='num'>{i['total_price']:,.2f} {currency}</td></tr>" for i in d.get('items',[]))
        return f"""<html><head><meta charset='utf-8'><style>
        body{{font-family:'Segoe UI','Tahoma',Arial,sans-serif;color:#172033;margin:0;background:#fff;}}
        .sheet{{padding:28px 34px;}} .top{{display:flex;justify-content:space-between;gap:24px;border-bottom:3px solid #2563eb;padding-bottom:18px;}}
        .brand h1{{margin:0;font-size:25px;color:#0f172a;}} .brand p{{margin:6px 0;color:#64748b;font-size:12px;}}
        .invoice-title{{text-align:left;}} .invoice-title h2{{margin:0;color:#2563eb;font-size:22px;}} .invoice-title p{{margin:5px 0;color:#64748b;font-size:12px;}}
        .meta{{margin:18px 0;padding:14px 16px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;}}
        .meta b{{color:#334155;}} table{{width:100%;border-collapse:collapse;margin-top:14px;}} th{{background:#eff6ff;color:#1e3a8a;text-align:right;padding:11px;border-bottom:1px solid #dbeafe;}} td{{padding:11px;border-bottom:1px solid #eef2f7;}} .num{{text-align:left;direction:ltr;}}
        .totals{{margin-top:18px;display:flex;justify-content:flex-end;}} .totalbox{{width:310px;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;}} .row{{display:flex;justify-content:space-between;padding:10px 14px;}} .grand{{background:#2563eb;color:#fff;font-weight:700;font-size:15px;}}
        .footer{{margin-top:24px;padding-top:14px;border-top:1px solid #e2e8f0;color:#64748b;font-size:11px;display:flex;justify-content:space-between;}}
        </style></head><body><div class='sheet'>
        <div class='top'><div class='brand'><h1>{org}</h1><p>فاتورة مبيعات</p></div><div class='invoice-title'><h2>#{d['invoice_number']}</h2><p>{d['sale_date'][:19]}</p></div></div>
        <div class='meta'><b>العميل:</b> {d.get('customer_name_ar') or 'عميل نقدي'} &nbsp;&nbsp; <b>الحالة:</b> {'مدفوع' if d.get('payment_status')=='paid' else 'جزئي' if d.get('payment_status')=='partial' else 'غير مدفوع'}</div>
        <table><tr><th>المنتج</th><th>الكمية</th><th>سعر الوحدة</th><th>الإجمالي</th></tr>{items}</table>
        <div class='totals'><div class='totalbox'><div class='row'><span>المجموع الفرعي</span><b>{d.get('subtotal',0):,.2f} {currency}</b></div><div class='row'><span>الخصم</span><b>{d.get('discount_amount',0):,.2f} {currency}</b></div><div class='row'><span>الضريبة</span><b>{d.get('tax_amount',0):,.2f} {currency}</b></div><div class='row'><span>الإجمالي</span><b>{d['total_amount']:,.2f} {currency}</b></div><div class='row'><span>المدفوع</span><b>{d['paid_amount']:,.2f} {currency}</b></div><div class='row'><span>المتبقي</span><b>{d['remaining_amount']:,.2f} {currency}</b></div><div class='row grand'><span>الصافي</span><span>{d['total_amount']:,.2f} {currency}</span></div></div></div>
        <div class='footer'><span>شكرًا لتعاملكم معنا</span><span>{org}</span></div></div></body></html>"""

    def _print_document(self, html, title):
        printer=QPrinter(QPrinter.PrinterMode.HighResolution); printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4)); doc=QTextDocument(); doc.setHtml(html)
        dlg=QPrintDialog(printer,self); dlg.setWindowTitle(title)
        if dlg.exec()==QDialog.DialogCode.Accepted: doc.print(printer)

    def _show_invoice_preview(self, html, title, auto_print=False):
        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.setMinimumSize(980, 760)
        lay = QVBoxLayout(dlg); lay.setContentsMargins(14,14,14,14); lay.setSpacing(10)
        browser = QTextBrowser(); browser.setOpenExternalLinks(False); browser.setHtml(html)
        browser.setStyleSheet("QTextBrowser{background:#eef2f7;border:1px solid #dbe3ee;border-radius:12px;padding:10px;}")
        lay.addWidget(browser,1)
        actions=QHBoxLayout()
        export_btn=QPushButton('📄 تصدير PDF'); export_btn.setObjectName('primaryAction')
        print_btn=QPushButton('🖨️ طباعة'); print_btn.setObjectName('secondaryAction')
        close_btn=QPushButton('إغلاق'); close_btn.setObjectName('ghostAction')
        actions.addWidget(export_btn); actions.addWidget(print_btn); actions.addWidget(close_btn); actions.addStretch()
        lay.addLayout(actions)
        def do_print():
            printer=QPrinter(QPrinter.PrinterMode.HighResolution); printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            pd=QPrintDialog(printer,dlg); pd.setWindowTitle(title)
            if pd.exec()==QDialog.DialogCode.Accepted:
                doc=QTextDocument(); doc.setHtml(html); doc.print(printer)
        def export_pdf():
            path,_=QFileDialog.getSaveFileName(dlg,'حفظ الفاتورة كـ PDF',f"{title.replace(' ','_')}.pdf",'PDF (*.pdf)')
            if not path:return
            printer=QPrinter(QPrinter.PrinterMode.HighResolution); printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat); printer.setOutputFileName(path); printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            doc=QTextDocument(); doc.setHtml(html); doc.print(printer)
            QMessageBox.information(dlg, 'تم التصدير', f'تم حفظ الفاتورة بنجاح:\n{path}')
        export_btn.clicked.connect(export_pdf); print_btn.clicked.connect(do_print); close_btn.clicked.connect(dlg.accept)
        if auto_print:
            QTimer.singleShot(120, do_print)
        dlg.exec()

    def _create_purchases_page(self) -> QWidget:
        page=QWidget(); layout=QVBoxLayout(page); layout.setContentsMargins(24,20,24,20); layout.setSpacing(12)
        toolbar,search=self._page_toolbar('📦 المشتريات','بحث برقم الفاتورة أو المورّد…','➕ فاتورة شراء جديدة',lambda:self._show_page('purchases'))
        layout.addLayout(toolbar)
        actions=QHBoxLayout(); newb=QPushButton('➕ إضافة شراء'); newb.setStyleSheet(self._semantic_button_style('success')); newb.clicked.connect(lambda:self._quick_create_purchase()); actions.addWidget(newb); payb=QPushButton('💸 دفعة لمورّد'); payb.setStyleSheet(self._semantic_button_style('warning')); payb.clicked.connect(lambda:self._supplier_payment_dialog()); actions.addWidget(payb); actions.addStretch(); layout.addLayout(actions)
        table=self._table(['رقم الفاتورة','المورّد','المبلغ','المدفوع','المتبقي','الحالة','التاريخ','الإجراءات']); table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed); table.setColumnWidth(7, 140); layout.addWidget(table,1)
        self.purchases_table=table; self.purchases_search=search; search.textChanged.connect(lambda q:self._refresh_purchases(q)); self._refresh_purchases(); return page

    def _refresh_purchases(self,query=''):
        ps=self.purchase_repo.get_all(limit=500); q=(query or '').lower().strip()
        if q: ps=[x for x in ps if q in str(x.get('invoice_number','')).lower() or q in str(x.get('supplier_name_ar') or '').lower()]
        t=self.purchases_table; t.setRowCount(len(ps))
        for r,x in enumerate(ps):
            vals=[x['invoice_number'],x.get('supplier_name_ar') or '-',f"﷼ {x['total_amount']:,.0f}",f"﷼ {x['paid_amount']:,.0f}",f"﷼ {x['remaining_amount']:,.0f}",{'paid':'مدفوع','partial':'جزئي','unpaid':'غير مدفوع'}.get(x['payment_status'],x['payment_status']),x['purchase_date'][:10]]
            for c,v in enumerate(vals): t.setItem(r,c,QTableWidgetItem(str(v)))
            pid = x['id']
            ab = self._action_row([
                self._action_icon_button('👁', 'info', lambda _, pid=pid: self._preview_purchase(pid), 'معاينة فاتورة الشراء'),
                self._action_icon_button('↔', 'primary', lambda _, pid=pid: self._show_purchase_details(pid), 'تفاصيل الفاتورة'),
                self._action_icon_button('✕', 'danger', lambda _, pid=pid: self._cancel_purchase(pid), 'إلغاء الفاتورة'),
            ])
            t.setCellWidget(r,7,ab)

    def _show_purchase_details(self,purchase_id):
        d=self.purchase_service.get_purchase_with_items(purchase_id)
        if not d:return
        lines=[f"رقم الفاتورة: {d['invoice_number']}",f"المورّد: {d.get('supplier_name_ar') or '-'}",'']+[f"{i['name_ar']} × {i['quantity']} = ﷼ {i['total_cost']:,.0f}" for i in d.get('items',[])]+['',f"الإجمالي: ﷼ {d['total_amount']:,.0f}",f"المدفوع: ﷼ {d['paid_amount']:,.0f}",f"المتبقي: ﷼ {d['remaining_amount']:,.0f}"]
        QMessageBox.information(self,'تفاصيل الشراء','\n'.join(lines))

    def _cancel_purchase(self,purchase_id):
        p=self.purchase_repo.get_by_id(purchase_id)
        if not p or p['status']!='completed': return
        if QMessageBox.question(self,'إلغاء الشراء','سيتم عكس المخزون ورصيد المورّد. متابعة؟')!=QMessageBox.StandardButton.Yes:return
        with self.db.transaction():
            for i in self.purchase_repo.get_items(purchase_id):
                self.product_repo.update_stock(i['product_id'],-i['quantity'])
                self.inventory_repo.record_movement(product_id=i['product_id'],movement_type='out',quantity=i['quantity'],reference_type='purchase_cancel',reference_id=purchase_id,created_by=self.user.id)
            if p.get('supplier_id') and p.get('remaining_amount',0)>0:self.supplier_repo.update_balance(p['supplier_id'],-p['remaining_amount'])
            self.accounting_service.reverse_purchase(purchase_id, self.user.id)
            self.purchase_repo.update(purchase_id,status='cancelled')
        self._refresh_purchases(self.purchases_search.text())

    def _print_purchase(self,purchase_id):
        self._preview_purchase(purchase_id, auto_print=True)
    def _preview_purchase(self,purchase_id, auto_print=False):
        d=self.purchase_service.get_purchase_with_items(purchase_id)
        if d:self._show_invoice_preview(self._purchase_html(d),f"معاينة فاتورة الشراء {d['invoice_number']}",auto_print=auto_print)
    def _purchase_html(self,d):
        org=self.settings_repo.get_default('org_name_ar', self.settings_repo.get_default('org_name','المنشأة')); currency=self.settings_repo.get_default('currency_symbol','ر.س')
        items=''.join(f"<tr><td>{i['name_ar']}</td><td class='num'>{i['quantity']:,.2f}</td><td class='num'>{i['unit_cost']:,.2f}</td><td class='num'>{i['total_cost']:,.2f} {currency}</td></tr>" for i in d.get('items',[]))
        return f"""<html><head><meta charset='utf-8'><style>body{{font-family:'Segoe UI','Tahoma',Arial,sans-serif;color:#172033;margin:0;}} .sheet{{padding:28px 34px;}} .top{{display:flex;justify-content:space-between;border-bottom:3px solid #10b981;padding-bottom:18px;}} .brand h1{{margin:0;font-size:25px;}} .brand p,.invoice-title p{{color:#64748b;font-size:12px;margin:6px 0;}} .invoice-title h2{{color:#059669;margin:0;font-size:22px;}} .meta{{margin:18px 0;padding:14px 16px;background:#f0fdf4;border:1px solid #d1fae5;border-radius:12px;}} table{{width:100%;border-collapse:collapse;}} th{{background:#ecfdf5;color:#065f46;text-align:right;padding:11px;}} td{{padding:11px;border-bottom:1px solid #eef2f7;}} .num{{text-align:left;direction:ltr;}} .totals{{margin-top:18px;display:flex;justify-content:flex-end;}} .totalbox{{width:310px;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;}} .row{{display:flex;justify-content:space-between;padding:10px 14px;}} .grand{{background:#059669;color:#fff;font-weight:700;}} .footer{{margin-top:24px;padding-top:14px;border-top:1px solid #e2e8f0;color:#64748b;font-size:11px;display:flex;justify-content:space-between;}}</style></head><body><div class='sheet'><div class='top'><div class='brand'><h1>{org}</h1><p>فاتورة مشتريات</p></div><div class='invoice-title'><h2>#{d['invoice_number']}</h2><p>{d['purchase_date'][:19]}</p></div></div><div class='meta'><b>المورّد:</b> {d.get('supplier_name_ar') or 'شراء نقدي'}</div><table><tr><th>المنتج</th><th>الكمية</th><th>تكلفة الوحدة</th><th>الإجمالي</th></tr>{items}</table><div class='totals'><div class='totalbox'><div class='row'><span>المجموع الفرعي</span><b>{d.get('subtotal',0):,.2f} {currency}</b></div><div class='row'><span>الخصم</span><b>{d.get('discount_amount',0):,.2f} {currency}</b></div><div class='row'><span>الضريبة</span><b>{d.get('tax_amount',0):,.2f} {currency}</b></div><div class='row'><span>الإجمالي</span><b>{d['total_amount']:,.2f} {currency}</b></div><div class='row'><span>المدفوع</span><b>{d['paid_amount']:,.2f} {currency}</b></div><div class='row'><span>المتبقي</span><b>{d['remaining_amount']:,.2f} {currency}</b></div><div class='row grand'><span>صافي الشراء</span><span>{d['total_amount']:,.2f} {currency}</span></div></div></div><div class='footer'><span>مستند مشتريات معتمد</span><span>{org}</span></div></div></body></html>"""
    def _quick_create_purchase(self):
        products=self.product_repo.get_all(); suppliers=self.supplier_repo.get_all()
        if not products: return QMessageBox.warning(self,'لا توجد منتجات','أضف منتجاً أولاً.')
        d=QDialog(self); d.setWindowTitle('إنشاء فاتورة شراء'); f=QFormLayout(d)
        supplier=QComboBox(); supplier.addItem('نقدي / بدون مورّد',None)
        for x in suppliers:supplier.addItem(x['name_ar'],x['id'])
        product=QComboBox()
        for x in products:product.addItem(f"{x['name_ar']} — ﷼ {x['cost_price']:,.0f}",x['id'])
        qty=QDoubleSpinBox();qty.setRange(0.01,1e9);qty.setValue(1);qty.setDecimals(2)
        cost=QDoubleSpinBox();cost.setRange(0,1e12);cost.setValue(products[0]['cost_price']);cost.setDecimals(2)
        product.currentIndexChanged.connect(lambda i: cost.setValue(products[i]['cost_price'] if 0<=i<len(products) else 0))
        paid=QDoubleSpinBox();paid.setRange(0,1e12);paid.setDecimals(2);notes=QLineEdit()
        for lab,w in [('المورّد',supplier),('المنتج',product),('الكمية',qty),('تكلفة الوحدة',cost),('المدفوع',paid),('ملاحظات',notes)]:f.addRow(lab,w)
        b=QPushButton('حفظ الفاتورة');f.addRow(b);b.clicked.connect(d.accept)
        if d.exec()!=QDialog.DialogCode.Accepted:return
        try:
            result=self.purchase_service.create_purchase(items=[{'product_id':product.currentData(),'quantity':qty.value(),'unit_cost':cost.value()}],supplier_id=supplier.currentData(),paid_amount=paid.value(),notes=notes.text().strip(),created_by=self.user.id)
            self._refresh_purchases(self.purchases_search.text())
            QMessageBox.information(self,'تم الحفظ',f"تم إنشاء {result['invoice_number']}\nالإجمالي: ﷼ {result['total_amount']:,.0f}\nالمتبقي: ﷼ {result['remaining']:,.0f}")
        except Exception as e:QMessageBox.critical(self,'خطأ',str(e))

    def _create_inventory_page(self) -> QWidget:
        page=QWidget(); layout=QVBoxLayout(page); layout.setContentsMargins(24,20,24,20); layout.setSpacing(12)
        toolbar,search=self._page_toolbar('📦 المخزون','بحث بالاسم أو الباركود…','➕ إضافة منتج',self._product_dialog)
        layout.addLayout(toolbar)
        actions=QHBoxLayout(); cb=QPushButton('🏷️ إدارة التصنيفات'); cb.setStyleSheet(self._semantic_button_style('info')); cb.clicked.connect(self._category_dialog); actions.addWidget(cb); adj=QPushButton('↕️ تسوية مخزون'); adj.setStyleSheet(self._semantic_button_style('warning')); adj.clicked.connect(self._inventory_adjustment_dialog); actions.addWidget(adj); actions.addStretch(); layout.addLayout(actions)
        table=self._table(['المنتج','الباركود','التصنيف','المخزون','الحد الأدنى','التكلفة','السعر','الانتهاء','الإجراءات']); layout.addWidget(table,1)
        self.inventory_table=table; self.inventory_search=search; search.textChanged.connect(lambda q:self._refresh_inventory(q)); self._refresh_inventory(); return page

    def _refresh_inventory(self,query=''):
        ps=self.product_repo.get_all(); q=(query or '').lower().strip()
        if q: ps=[x for x in ps if q in str(x.get('name_ar','')).lower() or q in str(x.get('name','')).lower() or q in str(x.get('barcode') or '').lower()]
        cats={c['id']:c['name_ar'] for c in self.category_repo.get_all(active_only=False)}; t=self.inventory_table; t.setRowCount(len(ps))
        for r,x in enumerate(ps):
            vals=[x['name_ar'],x.get('barcode') or '-',cats.get(x.get('category_id'),'-'),x['stock_quantity'],x['min_stock'],f"﷼ {x['cost_price']:,.0f}",f"﷼ {x['selling_price']:,.0f}",x.get('expiry_date') or '-']
            for c,v in enumerate(vals): t.setItem(r,c,QTableWidgetItem(str(v)))
            if x['stock_quantity']<=x['min_stock']: t.item(r,3).setForeground(QColor(COLORS['danger']))
            pid = x['id']
            w = self._action_row([
                self._action_icon_button('✎', 'primary', lambda _, pid=pid: self._product_dialog(pid), 'تعديل المنتج'),
                self._action_icon_button('🗑', 'danger', lambda _, pid=pid: self._delete_product(pid), 'حذف/إخفاء المنتج'),
            ])
            t.setCellWidget(r,8,w)

    def _product_dialog(self, product_id=None):
        old=self.product_repo.get_by_id(product_id) if product_id else None
        d=QDialog(self); d.setWindowTitle('تعديل منتج' if old else 'إضافة منتج'); form=QFormLayout(d)
        name=QLineEdit(old['name_ar'] if old else ''); en=QLineEdit(old['name'] if old else '')
        barcode=QLineEdit(old.get('barcode') or '' if old else ''); unit=QLineEdit(old.get('unit') or 'قطعة' if old else 'قطعة')
        cat=QComboBox(); cats=self.category_repo.get_all(active_only=True); cat.addItem('بدون تصنيف',None)
        for c in cats: cat.addItem(c['name_ar'],c['id'])
        if old: cat.setCurrentIndex(max(0,cat.findData(old.get('category_id'))))
        cost=QDoubleSpinBox(); cost.setMaximum(1e12); cost.setValue(old['cost_price'] if old else 0)
        price=QDoubleSpinBox(); price.setMaximum(1e12); price.setValue(old['selling_price'] if old else 0)
        stock=QDoubleSpinBox(); stock.setMaximum(1e12); stock.setValue(old['stock_quantity'] if old else 0)
        minimum=QDoubleSpinBox(); minimum.setMaximum(1e12); minimum.setValue(old['min_stock'] if old else 0)
        expiry=QLineEdit(old.get('expiry_date') or '' if old else '')
        for label,w in [('الاسم بالعربي',name),('الاسم',en),('الباركود',barcode),('الوحدة',unit),('التصنيف',cat),('التكلفة',cost),('سعر البيع',price),('الرصيد الحالي',stock),('الحد الأدنى',minimum),('تاريخ الانتهاء',expiry)]: form.addRow(label,w)
        bb=QHBoxLayout(); save=QPushButton('حفظ'); cancel=QPushButton('إلغاء'); save.clicked.connect(d.accept); cancel.clicked.connect(d.reject); bb.addWidget(save); bb.addWidget(cancel); form.addRow(bb)
        if d.exec()!=QDialog.DialogCode.Accepted:return
        if not name.text().strip(): QMessageBox.warning(self,'بيانات ناقصة','اكتب اسم المنتج.'); return
        data=dict(name_ar=name.text().strip(),name=en.text().strip() or name.text().strip(),barcode=barcode.text().strip() or None,unit=unit.text().strip() or 'piece',category_id=cat.currentData(),cost_price=cost.value(),selling_price=price.value(),stock_quantity=stock.value(),min_stock=minimum.value(),expiry_date=expiry.text().strip() or None)
        try:
            if old:self.product_repo.update(product_id,**data)
            else:self.product_repo.create(**data)
            self._refresh_inventory(self.inventory_search.text())
        except Exception as e: QMessageBox.critical(self,'خطأ',str(e))

    def _delete_product(self,pid):
        if QMessageBox.question(self,'حذف منتج','سيتم إخفاء المنتج مع الحفاظ على سجله المحاسبي. متابعة؟')==QMessageBox.StandardButton.Yes:
            self.product_repo.delete(pid); self._refresh_inventory(self.inventory_search.text())

    def _category_dialog(self):
        d=QDialog(self); d.setWindowTitle('التصنيفات'); l=QVBoxLayout(d); t=self._table(['الاسم العربي','الاسم','الحالة','إجراء']); l.addWidget(t); form=QHBoxLayout(); name=QLineEdit(); name.setPlaceholderText('اسم التصنيف بالعربي'); en=QLineEdit(); en.setPlaceholderText('Name'); add=QPushButton('➕ إضافة'); form.addWidget(name);form.addWidget(en);form.addWidget(add);l.addLayout(form)
        def load():
            cs=self.category_repo.get_all(active_only=False); t.setRowCount(len(cs))
            for r,c in enumerate(cs):
                t.setItem(r,0,QTableWidgetItem(c['name_ar']));t.setItem(r,1,QTableWidgetItem(c['name']));t.setItem(r,2,QTableWidgetItem('فعال' if c['is_active'] else 'غير فعال'));b=QPushButton('تعطيل');b.clicked.connect(lambda _,cid=c['id']:(self.category_repo.update(cid,is_active=0),load(),self._refresh_inventory(self.inventory_search.text())));t.setCellWidget(r,3,b)
        add.clicked.connect(lambda:(self.category_repo.create(name=en.text().strip() or name.text().strip(),name_ar=name.text().strip() or en.text().strip(),sort_order=999),load(),name.clear(),en.clear(),self._refresh_inventory(self.inventory_search.text())))
        load(); d.resize(650,500); d.exec()

    def _inventory_adjustment_dialog(self):
        d=QDialog(self); d.setWindowTitle('تسوية المخزون'); f=QFormLayout(d); p=QComboBox(); products=self.product_repo.get_all();
        for x in products:p.addItem(x['name_ar'],x['id'])
        qty=QDoubleSpinBox();qty.setRange(-1e9,1e9);qty.setDecimals(2);reason=QLineEdit(); reason.setPlaceholderText('سبب التسوية'); f.addRow('المنتج',p);f.addRow('الكمية + / -',qty);f.addRow('السبب',reason);b=QPushButton('حفظ');f.addRow(b);b.clicked.connect(d.accept)
        if d.exec()==QDialog.DialogCode.Accepted:
            q=qty.value(); pid=p.currentData()
            if q==0:return
            with self.db.transaction():
                self.product_repo.update_stock(pid,q); self.inventory_repo.record_movement(product_id=pid,movement_type='adjustment',quantity=q,notes=reason.text().strip(),created_by=self.user.id); self.accounting_service.post_inventory_adjustment(pid,q,self.user.id)
            self._refresh_inventory(self.inventory_search.text())

    def _create_customers_page(self) -> QWidget:
        page=QWidget(); layout=QVBoxLayout(page); layout.setContentsMargins(24,20,24,20); layout.setSpacing(12)
        toolbar,search=self._page_toolbar('👥 العملاء','بحث بالاسم أو الهاتف…','➕ إضافة عميل',self._customer_dialog);layout.addLayout(toolbar)
        actions=QHBoxLayout(); rec=QPushButton('💰 تحصيل ديون'); rec.setStyleSheet(self._semantic_button_style('success'));rec.clicked.connect(self._customer_payment_dialog);actions.addWidget(rec);exp=QPushButton('📤 تصدير'); exp.setStyleSheet(self._semantic_button_style('info'));exp.clicked.connect(lambda:self._export_table(self.customers_table,'customers'));actions.addWidget(exp);actions.addStretch();layout.addLayout(actions)
        t=self._table(['الاسم','الهاتف','الرصيد','حد الائتمان','ملاحظات','الإجراءات']);layout.addWidget(t,1);self.customers_table=t;self.customers_search=search;search.textChanged.connect(lambda q:self._refresh_customers(q));self._refresh_customers();return page

    def _refresh_customers(self,q=''):
        cs=self.customer_repo.get_all();q=(q or '').lower().strip(); cs=[x for x in cs if not q or q in str(x['name_ar']).lower() or q in str(x.get('phone') or '').lower()];t=self.customers_table;t.setRowCount(len(cs))
        for r,x in enumerate(cs):
            for c,v in enumerate([x['name_ar'],x.get('phone') or '-',f"﷼ {x['balance']:,.0f}",f"﷼ {x['credit_limit']:,.0f}",x.get('notes') or '-']):t.setItem(r,c,QTableWidgetItem(str(v)))
            cid = x['id']
            w = self._action_row([
                self._action_icon_button('✎', 'primary', lambda _, cid=cid: self._customer_dialog(cid), 'تعديل العميل'),
                self._action_icon_button('💰', 'success', lambda _, cid=cid: self._customer_payment_dialog(cid), 'تحصيل من العميل'),
                self._action_icon_button('🗑', 'danger', lambda _, cid=cid: self._delete_customer(cid), 'حذف/إخفاء العميل'),
            ])
            t.setCellWidget(r,5,w)

    def _customer_dialog(self,cid=None):
        old=self.customer_repo.get_by_id(cid) if cid else None;d=QDialog(self);d.setWindowTitle('تعديل عميل' if old else 'إضافة عميل');f=QFormLayout(d)
        n=QLineEdit(old['name_ar'] if old else '');en=QLineEdit(old['name'] if old else '');ph=QLineEdit(old.get('phone') or '' if old else '');email=QLineEdit(old.get('email') or '' if old else '');addr=QLineEdit(old.get('address_ar') or '' if old else '');limit=QDoubleSpinBox();limit.setMaximum(1e12);limit.setValue(old['credit_limit'] if old else 0);notes=QTextEdit(old.get('notes') or '' if old else '')
        for lab,w in [('الاسم',n),('الاسم اللاتيني',en),('الهاتف',ph),('البريد',email),('العنوان',addr),('حد الائتمان',limit),('ملاحظات',notes)]:f.addRow(lab,w)
        b=QPushButton('حفظ');b.clicked.connect(d.accept);f.addRow(b)
        if d.exec()!=QDialog.DialogCode.Accepted:return
        if not n.text().strip():QMessageBox.warning(self,'بيانات ناقصة','اكتب اسم العميل.');return
        data=dict(name_ar=n.text().strip(),name=en.text().strip() or n.text().strip(),phone=ph.text().strip() or None,email=email.text().strip() or None,address_ar=addr.text().strip() or None,address=addr.text().strip() or None,credit_limit=limit.value(),notes=notes.toPlainText().strip() or None)
        if old:self.customer_repo.update(cid,**data)
        else:self.customer_repo.create(**data)
        self._refresh_customers(self.customers_search.text())

    def _delete_customer(self,cid):
        if QMessageBox.question(self,'حذف','إخفاء العميل؟')==QMessageBox.StandardButton.Yes:self.customer_repo.delete(cid);self._refresh_customers(self.customers_search.text())

    def _customer_payment_dialog(self,cid=None): self._payment_dialog('customer',cid)

    def _create_suppliers_page(self) -> QWidget:
        page=QWidget();layout=QVBoxLayout(page);layout.setContentsMargins(24,20,24,20);layout.setSpacing(12)
        toolbar,search=self._page_toolbar('🏭 المورّدون','بحث بالاسم أو الهاتف…','➕ إضافة مورّد',self._supplier_dialog);layout.addLayout(toolbar)
        actions=QHBoxLayout();pay=QPushButton('💸 دفعة لمورّد'); pay.setStyleSheet(self._semantic_button_style('warning'));pay.clicked.connect(self._supplier_payment_dialog);actions.addWidget(pay);ex=QPushButton('📤 تصدير'); ex.setStyleSheet(self._semantic_button_style('info'));ex.clicked.connect(lambda:self._export_table(self.suppliers_table,'suppliers'));actions.addWidget(ex);actions.addStretch();layout.addLayout(actions)
        t=self._table(['الاسم','الهاتف','الرصيد المستحق','ملاحظات','الإجراءات']);layout.addWidget(t,1);self.suppliers_table=t;self.suppliers_search=search;search.textChanged.connect(lambda q:self._refresh_suppliers(q));self._refresh_suppliers();return page

    def _refresh_suppliers(self,q=''):
        ss=self.supplier_repo.get_all();q=(q or '').lower().strip();ss=[x for x in ss if not q or q in str(x['name_ar']).lower() or q in str(x.get('phone') or '').lower()];t=self.suppliers_table;t.setRowCount(len(ss))
        for r,x in enumerate(ss):
            for c,v in enumerate([x['name_ar'],x.get('phone') or '-',f"﷼ {x['balance']:,.0f}",x.get('notes') or '-']):t.setItem(r,c,QTableWidgetItem(str(v)))
            sid = x['id']
            w = self._action_row([
                self._action_icon_button('👁', 'info', lambda _, sid=sid: self._show_supplier_statement(sid), 'كشف حساب المورد'),
                self._action_icon_button('✎', 'primary', lambda _, sid=sid: self._supplier_dialog(sid), 'تعديل المورد'),
                self._action_icon_button('💸', 'warning', lambda _, sid=sid: self._supplier_payment_dialog(sid), 'دفع للمورد'),
                self._action_icon_button('🗑', 'danger', lambda _, sid=sid: self._delete_supplier(sid), 'حذف/إخفاء المورد'),
            ])
            t.setCellWidget(r,4,w)

    def _supplier_dialog(self,sid=None):
        old=self.supplier_repo.get_by_id(sid) if sid else None;d=QDialog(self);d.setWindowTitle('تعديل مورّد' if old else 'إضافة مورّد');f=QFormLayout(d);n=QLineEdit(old['name_ar'] if old else '');en=QLineEdit(old['name'] if old else '');ph=QLineEdit(old.get('phone') or '' if old else '');addr=QLineEdit(old.get('address_ar') or '' if old else '');notes=QTextEdit(old.get('notes') or '' if old else '')
        for lab,w in [('الاسم',n),('الاسم اللاتيني',en),('الهاتف',ph),('العنوان',addr),('ملاحظات',notes)]:f.addRow(lab,w)
        b=QPushButton('حفظ');b.clicked.connect(d.accept);f.addRow(b)
        if d.exec()!=QDialog.DialogCode.Accepted:return
        data=dict(name_ar=n.text().strip(),name=en.text().strip() or n.text().strip(),phone=ph.text().strip() or None,address_ar=addr.text().strip() or None,address=addr.text().strip() or None,notes=notes.toPlainText().strip() or None)
        if old:self.supplier_repo.update(sid,**data)
        else:self.supplier_repo.create(**data)
        self._refresh_suppliers(self.suppliers_search.text())

    def _delete_supplier(self,sid):
        if QMessageBox.question(self,'حذف','إخفاء المورّد؟')==QMessageBox.StandardButton.Yes:self.supplier_repo.delete(sid);self._refresh_suppliers(self.suppliers_search.text())


    def _statement_dialog(self, data, title):
        if not data: return
        d=QDialog(self); d.setWindowTitle(title); d.resize(920,560)
        lay=QVBoxLayout(d)
        head=QLabel(f"{data['party']['name_ar']} — الرصيد الحالي: ﷼ {data['balance']:,.2f}")
        head.setStyleSheet(f"font-size:13pt;font-weight:800;color:{COLORS['text']};")
        lay.addWidget(head)
        t=self._table(['التاريخ','النوع','المرجع','مدين','دائن','الرصيد'])
        lay.addWidget(t,1); t.setRowCount(len(data['rows']))
        for r,x in enumerate(data['rows']):
            vals=[str(x['date'])[:19],x['type'],x['reference'],f"﷼ {x['debit']:,.2f}",f"﷼ {x['credit']:,.2f}",f"﷼ {x['balance']:,.2f}"]
            for c,v in enumerate(vals): t.setItem(r,c,QTableWidgetItem(str(v)))
        row=QHBoxLayout(); ex=QPushButton('📤 تصدير الكشف CSV'); ex.setStyleSheet(self._semantic_button_style('info'))
        ex.clicked.connect(lambda:self._export_table(t,'statement')); row.addWidget(ex); row.addStretch()
        close=QPushButton('إغلاق'); close.clicked.connect(d.accept); row.addWidget(close); lay.addLayout(row)
        d.exec()

    def _show_customer_statement(self, customer_id):
        self._statement_dialog(self.reports_service.customer_statement(int(customer_id)), 'كشف حساب العميل')

    def _show_supplier_statement(self, supplier_id):
        self._statement_dialog(self.reports_service.supplier_statement(int(supplier_id)), 'كشف حساب المورد')

    def _supplier_payment_dialog(self,sid=None): self._payment_dialog('supplier',sid)

    def _payment_dialog(self,payment_type,party_id=None):
        d=QDialog(self); d.setWindowTitle('تحصيل من عميل' if payment_type=='customer' else 'دفعة للمورّد'); d.resize(520,420)
        f=QFormLayout(d)
        party=QComboBox(); rows=self.customer_repo.get_all() if payment_type=='customer' else self.supplier_repo.get_all()
        for x in rows:
            party.addItem(x['name_ar'],x['id'])
        if party_id is not None:
            party.setCurrentIndex(max(0,party.findData(party_id)))
        balance_lbl=QLabel('الرصيد: 0')
        def refresh_balance():
            row=(self.customer_repo.get_by_id(party.currentData()) if payment_type=='customer' else self.supplier_repo.get_by_id(party.currentData()))
            bal=float(row['balance']) if row else 0.0
            balance_lbl.setText(f"الرصيد الحالي: ﷼ {bal:,.2f}")
        party.currentIndexChanged.connect(refresh_balance)
        amount=QDoubleSpinBox(); amount.setMaximum(1e12); amount.setDecimals(2); amount.setMinimum(0.01)
        method=QComboBox(); method.addItem('نقدي','cash'); method.addItem('شبكة/بطاقة','card'); method.addItem('تحويل','transfer'); method.addItem('شيك','check')
        ref=QLineEdit(); notes=QLineEdit()
        for lab,w in [('الطرف',party),('الرصيد',balance_lbl),('المبلغ',amount),('طريقة الدفع',method),('المرجع',ref),('ملاحظات',notes)]: f.addRow(lab,w)
        b=QPushButton('تسجيل الدفعة'); f.addRow(b); b.clicked.connect(d.accept)
        refresh_balance()
        if d.exec()!=QDialog.DialogCode.Accepted or amount.value()<=0:return
        pid=party.currentData(); pay=amount.value()
        row=(self.customer_repo.get_by_id(pid) if payment_type=='customer' else self.supplier_repo.get_by_id(pid))
        bal=float(row['balance']) if row else 0.0
        if pay>bal+0.01:
            return QMessageBox.warning(self,'مبلغ غير صالح',f'الرصيد الحالي هو ﷼ {bal:,.2f}')
        try:
            with self.db.transaction():
                payment_id=self.payment_repo.create(payment_type=payment_type,party_id=pid,amount=pay,payment_method=method.currentData(),reference_number=ref.text().strip() or None,notes=notes.text().strip() or None,payment_date=datetime.now().isoformat(),created_by=self.user.id)
                remaining=pay
                if payment_type=='customer':
                    invoices=self.db.fetch_all("SELECT * FROM sales WHERE customer_id=? AND status='completed' AND remaining_amount>0 ORDER BY sale_date ASC,id ASC",(pid,))
                    for inv in invoices:
                        if remaining<=0.005: break
                        alloc=min(remaining,float(inv['remaining_amount']))
                        self.db.insert('payment_allocations',{'payment_id':payment_id,'invoice_type':'sale','invoice_id':inv['id'],'amount':alloc,'created_at':datetime.now().isoformat()})
                        self.sale_repo.update_payment(inv['id'],float(inv['paid_amount'])+alloc)
                        remaining-=alloc
                    self.customer_repo.update_balance(pid,-pay)
                    self.accounting_service.post_customer_payment(payment_id,self.user.id)
                    self._refresh_customers(self.customers_search.text())
                else:
                    invoices=self.db.fetch_all("SELECT * FROM purchases WHERE supplier_id=? AND status='completed' AND remaining_amount>0 ORDER BY purchase_date ASC,id ASC",(pid,))
                    for inv in invoices:
                        if remaining<=0.005: break
                        alloc=min(remaining,float(inv['remaining_amount']))
                        self.db.insert('payment_allocations',{'payment_id':payment_id,'invoice_type':'purchase','invoice_id':inv['id'],'amount':alloc,'created_at':datetime.now().isoformat()})
                        self.purchase_repo.update_payment(inv['id'],float(inv['paid_amount'])+alloc)
                        remaining-=alloc
                    self.supplier_repo.update_balance(pid,-pay)
                    self.accounting_service.post_supplier_payment(payment_id,self.user.id)
                    self._refresh_suppliers(self.suppliers_search.text())
            self._refresh_payments()
            QMessageBox.information(self,'تم التسجيل',f"تم تسجيل الدفعة بقيمة ﷼ {pay:,.2f} وتوزيعها على الفواتير المستحقة.")
        except Exception as e:
            QMessageBox.critical(self,'خطأ في الدفعة',str(e))

    def _create_payments_page(self):
        page=QWidget(); layout=QVBoxLayout(page); layout.setContentsMargins(24,20,24,20); layout.setSpacing(12)
        title=QLabel('💳 التحصيلات والدفعات'); title.setStyleSheet(f"font-size:15pt;font-weight:800;color:{COLORS['text']};"); layout.addWidget(title)
        actions=QHBoxLayout()
        cb=QPushButton('💰 تحصيل من عميل'); cb.setStyleSheet(self._semantic_button_style('success')); cb.clicked.connect(lambda:self._payment_dialog('customer')); actions.addWidget(cb)
        sb=QPushButton('💸 دفعة لمورّد'); sb.setStyleSheet(self._semantic_button_style('warning')); sb.clicked.connect(lambda:self._payment_dialog('supplier')); actions.addWidget(sb)
        ex=QPushButton('📤 تصدير'); ex.setStyleSheet(self._semantic_button_style('info')); ex.clicked.connect(lambda:self._export_table(self.payments_table,'payments')); actions.addWidget(ex); actions.addStretch(); layout.addLayout(actions)
        t=self._table(['النوع','الطرف','المبلغ','طريقة الدفع','المرجع','التاريخ','الفاتورة المرتبطة']); layout.addWidget(t,1)
        self.payments_table=t; self._refresh_payments(); return page

    def _refresh_payments(self):
        if not hasattr(self,'payments_table'): return
        rows=self.payment_repo.get_all(limit=500)
        t=self.payments_table; t.setRowCount(len(rows))
        for r,x in enumerate(rows):
            if x['payment_type']=='customer':
                party=self.customer_repo.get_by_id(x['party_id']); typ='تحصيل عميل'
                alloc=self.db.fetch_one("SELECT invoice_id FROM payment_allocations WHERE payment_id=? AND invoice_type='sale' ORDER BY id LIMIT 1",(x['id'],))
                inv=(self.sale_repo.get_by_id(alloc['invoice_id']) if alloc else None)
            else:
                party=self.supplier_repo.get_by_id(x['party_id']); typ='دفعة مورّد'
                alloc=self.db.fetch_one("SELECT invoice_id FROM payment_allocations WHERE payment_id=? AND invoice_type='purchase' ORDER BY id LIMIT 1",(x['id'],))
                inv=(self.purchase_repo.get_by_id(alloc['invoice_id']) if alloc else None)
            vals=[typ,party['name_ar'] if party else '-',f"﷼ {x['amount']:,.2f}",{'cash':'نقدي','card':'بطاقة','transfer':'تحويل','check':'شيك'}.get(x['payment_method'],x['payment_method']),x.get('reference_number') or '-',x['payment_date'][:19],inv['invoice_number'] if inv else '-']
            for c,v in enumerate(vals): t.setItem(r,c,QTableWidgetItem(str(v)))

    def _create_accounting_page(self):
        page=QWidget(); layout=QVBoxLayout(page); layout.setContentsMargins(24,20,24,20); layout.setSpacing(12)
        title=QLabel('🧾 المحاسبة'); title.setStyleSheet(f"font-size:15pt;font-weight:800;color:{COLORS['text']};"); layout.addWidget(title)
        hint=QLabel('الأرصدة أدناه مبنية من القيود المزدوجة الناتجة عن المبيعات والمشتريات والتحصيلات والدفعات.')
        hint.setStyleSheet(f"color:{COLORS['text_secondary']};"); layout.addWidget(hint)
        t=self._table(['الحساب','النوع','مدين','دائن','الرصيد']); layout.addWidget(t,1); self.accounting_table=t
        refresh=QPushButton('🔄 تحديث ميزان المراجعة'); refresh.setStyleSheet(self._semantic_button_style('primary')); refresh.clicked.connect(self._refresh_accounting); layout.addWidget(refresh,0,Qt.AlignmentFlag.AlignLeft)
        journal_title=QLabel('📒 آخر القيود المحاسبية'); journal_title.setStyleSheet(f'font-size:11pt;font-weight:700;color:{COLORS["text"]};'); layout.addWidget(journal_title)
        jt=self._table(['رقم القيد','التاريخ','الوصف','المصدر','الحالة']); layout.addWidget(jt,1); self.journal_table=jt
        self._refresh_accounting(); return page

    def _refresh_accounting(self):
        if not hasattr(self,'accounting_table'): return
        rows=self.accounting_repo.get_trial_balance(); t=self.accounting_table; t.setRowCount(len(rows))
        types={'asset':'أصل','liability':'التزام','equity':'حقوق ملكية','revenue':'إيراد','expense':'مصروف'}
        for r,x in enumerate(rows):
            vals=[f"{x['code']} — {x['name_ar']}",types.get(x['account_type'],x['account_type']),f"﷼ {x['debit']:,.2f}",f"﷼ {x['credit']:,.2f}",f"﷼ {x['balance']:,.2f}"]
            for c,v in enumerate(vals): t.setItem(r,c,QTableWidgetItem(str(v)))
        if hasattr(self,'journal_table'):
            entries=self.accounting_repo.get_entries(limit=100); jt=self.journal_table; jt.setRowCount(len(entries))
            for r,e in enumerate(entries):
                vals=[e['entry_number'],str(e['entry_date'])[:19],e.get('description') or '-',f"{e.get('source_type') or '-'}:{e.get('source_id') or ''}",e.get('status') or '-']
                for c,v in enumerate(vals): jt.setItem(r,c,QTableWidgetItem(str(v)))
    def _export_table(self,table,name):
        path,_=QFileDialog.getSaveFileName(self,'تصدير CSV',f'{name}.csv','CSV Files (*.csv)')
        if not path:return
        import csv
        with open(path,'w',newline='',encoding='utf-8-sig') as fh:
            w=csv.writer(fh);w.writerow([table.horizontalHeaderItem(c).text() for c in range(table.columnCount()) if table.horizontalHeaderItem(c)])
            for r in range(table.rowCount()):w.writerow([table.item(r,c).text() if table.item(r,c) else '' for c in range(table.columnCount())])
        QMessageBox.information(self,'تم التصدير',f'تم حفظ الملف:\n{path}')

    def _create_reports_page(self) -> QWidget:
        page=QWidget(); layout=QVBoxLayout(page); layout.setContentsMargins(24,20,24,20); layout.setSpacing(12)
        title=QLabel('📊 التقارير'); title.setStyleSheet(f"font-size:15pt;font-weight:800;color:{COLORS['text']};"); layout.addWidget(title)
        tabs=QTabWidget(); layout.addWidget(tabs,1)

        summary=QWidget(); sl=QVBoxLayout(summary)
        grid=QGridLayout(); grid.setSpacing(14)
        revenue=self.sale_repo.get_total_revenue(); purchases=self.purchase_repo.get_total_purchases()
        cogs_row=self.db.fetch_one("SELECT COALESCE(SUM(debit),0) cogs FROM journal_lines jl JOIN accounts a ON a.id=jl.account_id JOIN journal_entries je ON je.id=jl.journal_entry_id WHERE a.code='5000' AND je.status='posted'")
        cogs=float(cogs_row['cogs']) if cogs_row else purchases; profit=revenue-cogs
        data=[('إجمالي المبيعات',f'﷼ {revenue:,.0f}','💰',COLORS['primary']),('تكلفة البضاعة المباعة',f'﷼ {cogs:,.0f}','📦',COLORS['warning']),('مجمل الربح',f'﷼ {profit:,.0f}','📈',COLORS['success']),('ديون العملاء',f'﷼ {self.customer_repo.get_total_receivables():,.0f}','👥',COLORS['info']),('مستحقات المورّدين',f'﷼ {self.supplier_repo.get_total_payables():,.0f}','🏭',COLORS['danger']),('المدفوعات اليوم',f'﷼ {self.payment_repo.get_today_total():,.0f}','💳','#8b5cf6')]
        for i,(tt,val,ic,col) in enumerate(data): grid.addWidget(self._make_stat_card(tt,val,ic,col),i//3,i%3)
        sl.addLayout(grid)
        ex=QPushButton('📤 تصدير المبيعات CSV'); ex.setStyleSheet(self._semantic_button_style('info')); ex.clicked.connect(lambda:self._export_table(self.sales_table,'sales_report')); sl.addWidget(ex,0,Qt.AlignmentFlag.AlignLeft)
        tabs.addTab(summary,'ملخص')

        exp=QWidget(); el=QVBoxLayout(exp); er=QHBoxLayout(); days=QSpinBox(); days.setRange(1,3650); days.setValue(90); er.addWidget(QLabel('خلال الأيام:')); er.addWidget(days); ref=QPushButton('🔄 تحديث'); er.addWidget(ref); er.addStretch(); el.addLayout(er)
        et=self._table(['المنتج','الدفعة','الانتهاء','الكمية','الفرع']); el.addWidget(et,1); self.expiry_table=et
        def refresh_exp():
            rows=self.reports_service.expiring_lots(days.value()); et.setRowCount(len(rows))
            for r,x in enumerate(rows):
                vals=[x['product_name'],x['lot_number'],x['expiry_date'] or '-',f"{x['current_quantity']:,.2f}",x.get('branch_name') or '-']
                for c,v in enumerate(vals): et.setItem(r,c,QTableWidgetItem(str(v)))
        ref.clicked.connect(refresh_exp); days.valueChanged.connect(lambda _=0:refresh_exp()); refresh_exp(); tabs.addTab(exp,'قرب الانتهاء')

        low=QWidget(); ll=QVBoxLayout(low); lt=self._table(['المنتج','الباركود','المخزون','الحد الأدنى','التكلفة','سعر البيع']); ll.addWidget(lt,1)
        rows=self.reports_service.low_stock(); lt.setRowCount(len(rows))
        for r,x in enumerate(rows):
            vals=[x['name_ar'],x.get('barcode') or '-',f"{x['stock_quantity']:,.2f}",f"{x.get('min_stock') or 0:,.2f}",f"﷼ {x['cost_price']:,.2f}",f"﷼ {x['selling_price']:,.2f}"]
            for c,v in enumerate(vals): lt.setItem(r,c,QTableWidgetItem(str(v)))
        tabs.addTab(low,'المخزون المنخفض')

        audit=QWidget(); al=QVBoxLayout(audit); at=self._table(['المستخدم','العملية','الكيان','المعرف','التفاصيل','التاريخ']); al.addWidget(at,1)
        ar=self.reports_service.audit_events(); at.setRowCount(len(ar))
        for r,x in enumerate(ar):
            vals=[x.get('username') or '-',x.get('action') or '-',x.get('entity_type') or '-',x.get('entity_id') or '-',x.get('details') or '-',str(x.get('created_at') or '')[:19]]
            for c,v in enumerate(vals): at.setItem(r,c,QTableWidgetItem(str(v)))
        tabs.addTab(audit,'سجل العمليات')
        return page

    def _create_settings_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)
        
        title = QLabel("⚙️ الإعدادات")
        title.setStyleSheet(f"font-size: 14pt; font-weight: 700; color: {COLORS['text']};")
        layout.addWidget(title)
        
        # Organization card
        org_card = self._make_card()
        org_layout = QVBoxLayout(org_card)
        org_layout.setContentsMargins(20, 16, 20, 16)
        org_layout.setSpacing(12)
        
        org_title = QLabel("🏢 معلومات المنشأة")
        org_title.setStyleSheet(f"font-size: 11pt; font-weight: 700; color: {COLORS['text']};")
        org_layout.addWidget(org_title)
        
        org_name = self.settings_repo.get_default('org_name', 'المنشأة')
        currency = self.settings_repo.get_default('currency', 'SAR')
        tax = self.settings_repo.get_default('tax_rate', '15')
        
        for label, value in [("المنشأة", org_name), ("العملة", currency), ("الضريبة", f"{tax}%")]:
            row = QHBoxLayout()
            lbl = QLabel(f"<b>{label}:</b>"); lbl.setStyleSheet(f"color:{COLORS['text']};"); row.addWidget(lbl)
            row.addStretch()
            val_lbl = QLabel(str(value)); val_lbl.setStyleSheet(f"color:{COLORS['text']};"); row.addWidget(val_lbl)
            org_layout.addLayout(row)
        
        layout.addWidget(org_card)
        
        # Appearance / theme card
        theme_card = self._make_card()
        theme_layout = QVBoxLayout(theme_card)
        theme_layout.setContentsMargins(20, 16, 20, 16)
        theme_layout.setSpacing(10)
        theme_title = QLabel('🎨 المظهر والسمات')
        theme_title.setStyleSheet(f"font-size: 11pt; font-weight: 700; color: {COLORS['text']};")
        theme_layout.addWidget(theme_title)
        desc = QLabel('اختر الوضع النهاري أو الليلي، ثم لون السمة الرئيسية. جميع النصوص والأزرار تستخدم تباينًا آمنًا تلقائيًا.')
        desc.setWordWrap(True); desc.setStyleSheet(f"color:{COLORS['text_secondary']}; font-size:9pt;")
        theme_layout.addWidget(desc)
        row = QHBoxLayout()
        mode_combo = QComboBox(); mode_combo.addItem('☀️ الوضع النهاري', 'light'); mode_combo.addItem('🌙 الوضع الليلي', 'dark')
        mode_combo.setCurrentIndex(0 if self.theme_mode == 'light' else 1)
        mode_lbl = QLabel('الوضع:'); mode_lbl.setStyleSheet(f"color:{COLORS['text']}; font-weight:600;"); row.addWidget(mode_lbl); row.addWidget(mode_combo)
        accent_combo = QComboBox()
        accent_labels = {'indigo':'بنفسجي نيلي','blue':'أزرق','emerald':'زمردي','violet':'بنفسجي','rose':'وردي','amber':'كهرماني'}
        for key,label in accent_labels.items(): accent_combo.addItem(label, key)
        idx = list(accent_labels).index(self.theme_accent) if self.theme_accent in accent_labels else 0
        accent_combo.setCurrentIndex(idx)
        accent_lbl = QLabel('لون الأزرار:'); accent_lbl.setStyleSheet(f"color:{COLORS['text']}; font-weight:600;"); row.addWidget(accent_lbl); row.addWidget(accent_combo)
        row.addStretch(); theme_layout.addLayout(row)
        contrast = QLabel('✓ تباين النص: مرتفع  •  ✓ الأزرار الأساسية: لون السمة  •  ✓ أزرار الخطر/النجاح لها ألوان مستقلة')
        contrast.setStyleSheet(f"color:{COLORS['success']}; font-size:9pt; font-weight:600;")
        theme_layout.addWidget(contrast)
        apply_btn = QPushButton('✨ تطبيق المظهر')
        apply_btn.clicked.connect(lambda: self._apply_theme_settings(mode_combo.currentData(), accent_combo.currentData()))
        theme_layout.addWidget(apply_btn, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(theme_card)

        # Backup card
        backup_card = self._make_card()
        backup_layout = QVBoxLayout(backup_card)
        backup_layout.setContentsMargins(20, 16, 20, 16)
        backup_layout.setSpacing(12)
        
        backup_title = QLabel("💾 النسخ الاحتياطي")
        backup_title.setStyleSheet(f"font-size: 11pt; font-weight: 700; color: {COLORS['text']};")
        backup_layout.addWidget(backup_title)
        
        btn_row = QHBoxLayout()
        create_btn = QPushButton("💾 إنشاء نسخة احتياطية")
        create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        create_btn.setStyleSheet(self._semantic_button_style('primary'))
        create_btn.clicked.connect(self._create_backup)
        btn_row.addWidget(create_btn)
        btn_row.addStretch()
        backup_layout.addLayout(btn_row)
        
        layout.addWidget(backup_card)
        layout.addStretch()
        return page
    
    def _apply_theme_settings(self, mode, accent):
        mode = mode if mode in THEMES else 'light'
        accent = accent if accent in ACCENTS else 'indigo'
        self.settings_repo.set('theme', mode, 'display')
        self.settings_repo.set('accent_color', accent, 'display')
        self.theme_mode, self.theme_accent = mode, accent
        COLORS.clear(); COLORS.update(palette(mode, accent))
        # Rebuild only the visual shell; business services and DB remain untouched.
        current = next((pid for pid, btn in self.nav_buttons.items() if btn.isChecked()), 'settings')
        old_central = self.centralWidget()
        if old_central is not None:
            old_central.deleteLater()
        self.setStyleSheet(build_styles(mode, accent))
        self._setup_ui()
        self._setup_status_bar()
        self._show_page(current)
        self.statusBar().showMessage('تم تطبيق المظهر بنجاح', 3500)

    def _create_backup(self):
        success, path, error = self.backup_service.create_backup()
        if success:
            QMessageBox.information(self, "نجاح", f"تم إنشاء النسخة الاحتياطية:\n{path}")
        else:
            QMessageBox.critical(self, "خطأ", f"فشل إنشاء النسخة:\n{error}")
    
    def _setup_status_bar(self):
        status_bar = QStatusBar()
        status_bar.setStyleSheet(f"""
            QStatusBar {{
                background: {COLORS['surface']}; border-top: 1px solid {COLORS['border']};
                padding: 4px 12px; font-size: 8pt;
            }}
        """)
        self.setStatusBar(status_bar)
        
        db_label = QLabel(f"📁 {self.settings.db_path}")
        db_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        status_bar.addWidget(db_label, 1)
        
        self.sync_label = QLabel("🟢 محلي — بدون اتصال سحابي")
        self.sync_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        status_bar.addPermanentWidget(self.sync_label)
    
    def _setup_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_datetime)
        self.timer.start(1000)
        self._update_datetime()
    
    def _update_datetime(self):
        now = datetime.now()
        self.datetime_label.setText(now.strftime("%Y-%m-%d  %H:%M:%S"))
    
    def _show_page(self, page_id: str):
        page_titles = {
            'dashboard': '🏠 لوحة التحكم',
            'pos': '💰 نقطة البيع',
            'sales': '📋 المبيعات',
            'purchases': '📦 المشتريات',
            'inventory': '📦 المخزون',
            'customers': '👥 العملاء',
            'suppliers': '🏭 المورّدون',
            'payments': '💳 التحصيلات والدفعات',
            'reports': '📊 التقارير',
            'accounting': '🧾 المحاسبة',
            'settings': '⚙️ الإعدادات',
        }
        
        for pid, btn in self.nav_buttons.items():
            btn.setChecked(pid == page_id)
        
        self.page_title.setText(page_titles.get(page_id, page_id))
        
        if page_id in self.pages:
            idx = list(self.pages.keys()).index(page_id)
            self.content_area.setCurrentIndex(idx)
            
            # Refresh data on page show
            if page_id == 'dashboard':
                pass  # Could refresh stats
    
    def _on_logout(self):
        reply = QMessageBox.question(
            self, "تسجيل الخروج",
            "هل تريد تسجيل الخروج؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.close()
    
    def closeEvent(self, event):
        self.timer.stop()
        self.db.close()
        event.accept()
