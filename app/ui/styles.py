"""Modern, high-contrast application themes for the Arabic-first UI."""

THEMES = {
    'light': {
        'background': '#f4f7fb', 'surface': '#ffffff', 'sidebar': '#111827',
        'sidebar_hover': '#1f2937', 'sidebar_active': '#4f46e5', 'text': '#172033', 'text_secondary': '#52627a',
        'text_muted': '#8491a7', 'border': '#d9e1ec', 'border_light': '#edf1f6',
        'input': '#ffffff', 'table_alt': '#f8fafc', 'shadow': '#0f172a',
    },
    'dark': {
        'background': '#0f172a', 'surface': '#172033', 'sidebar': '#020617',
        'sidebar_hover': '#1e293b', 'sidebar_active': '#4f46e5', 'text': '#f8fafc', 'text_secondary': '#c5d0df',
        'text_muted': '#94a3b8', 'border': '#334155', 'border_light': '#243247',
        'input': '#1e293b', 'table_alt': '#1a2537', 'shadow': '#000000',
    },
}

ACCENTS = {
    'indigo': ('#4f46e5', '#4338ca', '#eef2ff'),
    'blue': ('#2563eb', '#1d4ed8', '#eff6ff'),
    'emerald': ('#059669', '#047857', '#ecfdf5'),
    'violet': ('#7c3aed', '#6d28d9', '#f5f3ff'),
    'rose': ('#e11d48', '#be123c', '#fff1f2'),
    'amber': ('#d97706', '#b45309', '#fffbeb'),
}


def palette(mode='light', accent='indigo'):
    t = THEMES.get(mode, THEMES['light'])
    primary, primary_dark, primary_light = ACCENTS.get(accent, ACCENTS['indigo'])
    return {
        **t,
        'primary': primary, 'primary_dark': primary_dark, 'primary_light': primary_light,
        'sidebar_active': primary,
        'secondary': '#64748b', 'success': '#10b981', 'success_light': '#d1fae5',
        'danger': '#ef4444', 'danger_light': '#fee2e2', 'warning': '#f59e0b',
        'warning_light': '#fef3c7', 'info': '#0ea5e9', 'info_light': '#e0f2fe',
        'success_dark': '#059669', 'danger_dark': '#dc2626', 'warning_dark': '#d97706', 'info_dark': '#0284c7',
    }

COLORS = palette()


def build_styles(mode='light', accent='indigo'):
    c = palette(mode, accent)
    return f"""
    QWidget {{ font-family: 'Segoe UI', 'Tahoma', 'Arial', sans-serif; font-size: 10.8pt; color: {c['text']}; }}
    QMainWindow {{ background: {c['background']}; }}
    QFrame {{ color: {c['text']}; }}
    QLabel, QRadioButton, QCheckBox, QGroupBox, QAbstractButton {{ color: {c['text']}; }}
    QToolButton {{ color: {c['text']}; background: {c['surface']}; border: 1px solid {c['border']}; border-radius: 8px; padding: 6px 10px; }}
    QToolButton:hover {{ background: {c['primary_light']}; color: {c['primary_dark']}; }}
    QStatusBar {{ background: {c['surface']}; border-top: 1px solid {c['border']}; padding: 4px 12px; color: {c['text_secondary']}; }}
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit, QDateEdit {{
        background: {c['input']}; color: {c['text']}; border: 1px solid {c['border']};
        border-radius: 8px; padding: 8px 12px; selection-background-color: {c['primary_light']};
        selection-color: {c['text']};
        font-family: 'Segoe UI', 'Tahoma', 'Arial', sans-serif;
    }}
    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QTextEdit:focus, QDateEdit:focus {{ border: 2px solid {c['primary']}; }}
    QTableWidget, QTableView {{
        background: {c['surface']}; color: {c['text']}; border: 1px solid {c['border']};
        gridline-color: {c['border_light']}; selection-background-color: {c['primary_light']};
        selection-color: {c['text']}; alternate-background-color: {c['table_alt']};
    }}
    QHeaderView::section {{ background: {c['table_alt']}; color: {c['text']}; padding: 9px 12px; border: none; border-bottom: 2px solid {c['border']}; font-weight: 700; }}
    QPushButton {{ background: {c['surface']}; color: {c['text']}; border: 1px solid {c['border']}; border-radius: 9px; padding: 8px 18px; min-height: 34px; font-weight: 700; }}
    QPushButton:hover {{ background: {c['primary_light']}; color: {c['primary_dark']}; border-color: {c['primary']}; }}
    QPushButton:disabled {{ background: {c['border_light']}; color: {c['text_muted']}; border-color: {c['border']}; }}
    QPushButton:pressed {{ background: {c['primary']}; color: white; }}
    QCheckBox {{ color: {c['text']}; spacing: 8px; }}
    QGroupBox {{ color: {c['text']}; border: 1px solid {c['border']}; border-radius: 10px; margin-top: 12px; padding-top: 16px; }}
    QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top right; padding: 0 8px; color: {c['text_secondary']}; }}
    QTabWidget::pane {{ background: {c['surface']}; border: 1px solid {c['border']}; border-radius: 8px; }}
    QTabBar::tab {{ background: {c['background']}; color: {c['text_secondary']}; padding: 8px 16px; border: 1px solid {c['border']}; }}
    QTabBar::tab:selected {{ background: {c['surface']}; color: {c['primary']}; border-bottom: 2px solid {c['primary']}; }}
    QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{ background: #94a3b8; border-radius: 5px; min-height: 28px; }}
    QToolTip {{ background: {c['sidebar']}; color: white; border: none; padding: 6px 10px; border-radius: 5px; }}
    QMessageBox {{ background: {c['surface']}; }} QMessageBox QLabel {{ color: {c['text']}; background: transparent; }}
    """

MAIN_STYLESHEET = build_styles()
LOGIN_STYLESHEET = MAIN_STYLESHEET + """
#loginWindow { background: #0f172a; }
#loginCard { background: white; border-radius: 16px; padding: 32px; }
#loginTitle { font-size: 18pt; font-weight: 700; color: #172033; }
#loginSubtitle { font-size: 10pt; color: #52627a; }
QPushButton#loginButton { background: #4f46e5; color: white; border: none; border-radius: 10px; padding: 12px; font-size: 12pt; font-weight: 700; }
QPushButton#loginButton:hover { background: #4338ca; }
QLabel#errorLabel { color: #ef4444; font-weight: 600; }
"""
