"""
Modern login window with demo accounts.
"""
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QScrollArea,
    QApplication, QGridLayout, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QIcon, QPalette, QColor

from app.services.auth_service import AuthService
from app.services.demo_data_service import DemoDataService
from app.config.settings import AppSettings
from app.utils.i18n import t
from app.ui.styles import COLORS


logger = logging.getLogger(__name__)


# Demo account definitions
DEMO_ACCOUNTS = [
    {
        'username': 'supermarket',
        'password': 'demo123',
        'business_type': 'supermarket',
        'label_ar': 'سوبرماركت',
        'label_en': 'Supermarket',
        'icon': '🛒',
        'color': '#10b981',
        'description_ar': 'بقالة، مشروبات، منظفات',
    },
    {
        'username': 'pharmacy',
        'password': 'demo123',
        'business_type': 'pharmacy',
        'label_ar': 'صيدلية',
        'label_en': 'Pharmacy',
        'icon': '💊',
        'color': '#3b82f6',
        'description_ar': 'أدوية، مستلزمات طبية',
    },
    {
        'username': 'restaurant',
        'password': 'demo123',
        'business_type': 'restaurant',
        'label_ar': 'مطعم',
        'label_en': 'Restaurant',
        'icon': '🍽️',
        'color': '#f59e0b',
        'description_ar': 'أطباق، مشروبات، حلويات',
    },
    {
        'username': 'hotel',
        'password': 'demo123',
        'business_type': 'hotel',
        'label_ar': 'فندق',
        'label_en': 'Hotel',
        'icon': '🏨',
        'color': '#8b5cf6',
        'description_ar': 'غرف، خدمات،ضيافة',
    },
]


class DemoAccountCard(QFrame):
    """Clickable demo account card."""
    
    clicked = Signal(str, str, str)  # username, password, business_type
    
    def __init__(self, account: dict, parent=None):
        super().__init__(parent)
        self.account = account
        self._setup_ui()
    
    def _setup_ui(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(f"""
            DemoAccountCard {{
                background-color: white;
                border: 2px solid {COLORS['border']};
                border-radius: 12px;
                padding: 12px;
            }}
            DemoAccountCard:hover {{
                border-color: {self.account['color']};
                background-color: {COLORS['primary_light']};
            }}
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(110)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)
        
        # Icon + Name row
        top_row = QHBoxLayout()
        icon_label = QLabel(self.account['icon'])
        icon_label.setStyleSheet(f"font-size: 22pt; background: transparent; border: none;")
        top_row.addWidget(icon_label)
        
        name_label = QLabel(self.account['label_ar'])
        name_label.setStyleSheet(f"""
            font-size: 12pt; font-weight: 700; color: {self.account['color']};
            background: transparent; border: none;
        """)
        top_row.addWidget(name_label)
        top_row.addStretch()
        
        layout.addLayout(top_row)
        
        # Description
        desc = QLabel(self.account['description_ar'])
        desc.setStyleSheet(f"font-size: 8pt; color: {COLORS['text_secondary']}; background: transparent; border: none;")
        layout.addWidget(desc)
        
        # Credentials
        creds = QLabel(f"👤 {self.account['username']}  |  🔑 {self.account['password']}")
        creds.setStyleSheet(f"font-size: 8pt; color: {COLORS['text_muted']}; background: transparent; border: none;")
        layout.addWidget(creds)
    
    def mousePressEvent(self, event):
        self.clicked.emit(
            self.account['username'],
            self.account['password'],
            self.account['business_type']
        )
        super().mousePressEvent(event)


class LoginWindow(QWidget):
    """Modern login window with demo accounts."""
    
    login_successful = Signal(object, str)  # User, business_type
    
    def __init__(self, auth_service: AuthService, settings: AppSettings):
        super().__init__()
        self.auth_service = auth_service
        self.settings = settings
        self.demo_service = DemoDataService(auth_service.db)
        self._current_business_type = 'default'
        
        self._setup_ui()
        self._ensure_default_admin()
    
    def _ensure_default_admin(self):
        """Ensure default admin exists and create demo accounts."""
        self.auth_service.ensure_default_admin()
        
        # Create demo user accounts if they don't exist
        for demo in DEMO_ACCOUNTS:
            existing = self.auth_service.user_repo.get_by_username(demo['username'])
            if not existing:
                self.auth_service.create_user(
                    username=demo['username'],
                    display_name=demo['label_ar'],
                    password=demo['password'],
                    role='admin',
                )
    
    def _setup_ui(self):
        self.setWindowTitle(t('app_name'))
        self.setFixedSize(900, 620)
        self.setStyleSheet(f"""
            QWidget {{
                font-family: 'Cairo', 'Segoe UI', sans-serif;
                background-color: {COLORS['sidebar']};
            }}
        """)
        
        # Set window icon
        self._set_window_icon()
        
        # Center on screen
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Left panel - branding
        left_panel = QFrame()
        left_panel.setFixedWidth(380)
        left_panel.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1e40af, stop:1 #3b82f6);
            }}
        """)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.setContentsMargins(40, 40, 40, 40)
        
        # App icon
        icon_label = QLabel("📊")
        icon_label.setStyleSheet("font-size: 48pt; background: transparent;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(icon_label)
        
        left_layout.addSpacing(20)
        
        # App name
        title = QLabel("نظام المحاسبة")
        title.setStyleSheet("""
            font-size: 22pt; font-weight: 800; color: white;
            background: transparent;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(title)
        
        subtitle = QLabel("وإدارة الأعمال")
        subtitle.setStyleSheet("""
            font-size: 16pt; font-weight: 600; color: rgba(255,255,255,0.8);
            background: transparent;
        """)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(subtitle)
        
        left_layout.addSpacing(30)
        
        # Features list
        features = [
            "✅ نقطة بيع سريعة",
            "✅ إدارة المخزون",
            "✅ تقارير شاملة",
            "✅ فواتير احترافية",
            "✅ عمل بدون إنترنت",
        ]
        for feature in features:
            f_label = QLabel(feature)
            f_label.setStyleSheet("""
                font-size: 10pt; color: rgba(255,255,255,0.9);
                background: transparent; padding: 4px 0;
            """)
            left_layout.addWidget(f_label)
        
        left_layout.addStretch()
        
        version = QLabel(f"الإصدار {self.settings.app_version}")
        version.setStyleSheet("font-size: 8pt; color: rgba(255,255,255,0.5); background: transparent;")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(version)
        
        main_layout.addWidget(left_panel)
        
        # Right panel - login form + demo accounts
        right_panel = QFrame()
        right_panel.setStyleSheet(f"QFrame {{ background-color: white; }}")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(40, 30, 40, 30)
        right_layout.setSpacing(16)
        
        # Title
        login_title = QLabel("تسجيل الدخول")
        login_title.setStyleSheet(f"font-size: 18pt; font-weight: 700; color: {COLORS['text']};")
        right_layout.addWidget(login_title)
        
        login_subtitle = QLabel("أدخل بيانات الدخول أو اختر حساب تجريبي")
        login_subtitle.setStyleSheet(f"font-size: 9pt; color: {COLORS['text_secondary']};")
        right_layout.addWidget(login_subtitle)
        
        right_layout.addSpacing(8)
        
        # Username field
        u_label = QLabel("اسم المستخدم")
        u_label.setStyleSheet(f"font-size: 9pt; font-weight: 600; color: {COLORS['text_secondary']};")
        right_layout.addWidget(u_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("أدخل اسم المستخدم")
        self.username_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 10px 14px; border: 2px solid {COLORS['border']};
                border-radius: 10px; font-size: 11pt; background: white;
            }}
            QLineEdit:focus {{ border-color: {COLORS['primary']}; }}
        """)
        right_layout.addWidget(self.username_input)
        
        # Password field
        p_label = QLabel("كلمة المرور")
        p_label.setStyleSheet(f"font-size: 9pt; font-weight: 600; color: {COLORS['text_secondary']};")
        right_layout.addWidget(p_label)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("أدخل كلمة المرور")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 10px 14px; border: 2px solid {COLORS['border']};
                border-radius: 10px; font-size: 11pt; background: white;
            }}
            QLineEdit:focus {{ border-color: {COLORS['primary']}; }}
        """)
        right_layout.addWidget(self.password_input)
        
        # Error label
        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"font-size: 9pt; color: {COLORS['danger']}; font-weight: 500;")
        self.error_label.hide()
        right_layout.addWidget(self.error_label)
        
        # Login button
        self.login_button = QPushButton("دخول")
        self.login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']}; color: white;
                border: none; border-radius: 10px; padding: 12px;
                font-size: 12pt; font-weight: 700;
            }}
            QPushButton:hover {{ background-color: {COLORS['primary_dark']}; }}
            QPushButton:pressed {{ background-color: #1e40af; }}
        """)
        self.login_button.clicked.connect(self._on_login)
        right_layout.addWidget(self.login_button)
        
        right_layout.addSpacing(12)
        
        # Demo accounts separator
        sep_layout = QHBoxLayout()
        line1 = QFrame()
        line1.setFixedHeight(1)
        line1.setStyleSheet(f"background-color: {COLORS['border']};")
        sep_layout.addWidget(line1, 1)
        
        sep_label = QLabel("حسابات تجريبية")
        sep_label.setStyleSheet(f"font-size: 8pt; color: {COLORS['text_muted']}; padding: 0 10px;")
        sep_layout.addWidget(sep_label)
        
        line2 = QFrame()
        line2.setFixedHeight(1)
        line2.setStyleSheet(f"background-color: {COLORS['border']};")
        sep_layout.addWidget(line2, 1)
        
        right_layout.addLayout(sep_layout)
        
        # Demo accounts grid
        demo_grid = QGridLayout()
        demo_grid.setSpacing(10)
        
        for i, account in enumerate(DEMO_ACCOUNTS):
            card = DemoAccountCard(account)
            card.clicked.connect(self._on_demo_clicked)
            row = i // 2
            col = i % 2
            demo_grid.addWidget(card, row, col)
        
        right_layout.addLayout(demo_grid)
        right_layout.addStretch()
        
        main_layout.addWidget(right_panel, 1)
        
        # Connect Enter key
        self.password_input.returnPressed.connect(self._on_login)
        self.username_input.returnPressed.connect(lambda: self.password_input.setFocus())
        self.username_input.setFocus()
    
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
    
    def _on_demo_clicked(self, username: str, password: str, business_type: str):
        """Handle demo account card click."""
        self.username_input.setText(username)
        self.password_input.setText(password)
        self._current_business_type = business_type
        self._on_login()
    
    def _on_login(self):
        """Handle login."""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            self._show_error("يرجى إدخال اسم المستخدم وكلمة المرور")
            return
        
        self.login_button.setEnabled(False)
        self.login_button.setText("جاري الدخول...")
        self.error_label.hide()
        
        success, user, session, error = self.auth_service.login(username, password)
        
        if success:
            # Resolve the business type immediately, but NEVER generate demo
            # data here. Data generation can execute many SQLite writes and
            # must not block the Qt UI thread during login. The main entry
            # point schedules it after the main window is visible.
            business_type = self._current_business_type
            if username in [d['username'] for d in DEMO_ACCOUNTS]:
                for demo in DEMO_ACCOUNTS:
                    if demo['username'] == username:
                        business_type = demo['business_type']
                        break

            self.login_successful.emit(user, business_type)
        else:
            self._show_error(error)
            self.login_button.setEnabled(True)
            self.login_button.setText("دخول")
            self.password_input.clear()
            self.password_input.setFocus()
    
    def _generate_demo_data(self, business_type: str):
        """Generate demo data for the selected business type."""
        try:
            if business_type == 'supermarket':
                self.demo_service.generate_supermarket_data()
            elif business_type == 'pharmacy':
                self.demo_service.generate_pharmacy_data()
            elif business_type == 'restaurant':
                self.demo_service.generate_restaurant_data()
            elif business_type == 'hotel':
                self.demo_service.generate_hotel_data()
            logger.info(f"Demo data generated for: {business_type}")
        except Exception as e:
            logger.error(f"Failed to generate demo data: {e}")
    
    def _show_error(self, message: str):
        self.error_label.setText(message)
        self.error_label.show()
