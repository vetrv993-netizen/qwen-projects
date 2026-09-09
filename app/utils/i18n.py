"""
Internationalization (i18n) module.

Provides Arabic-first translation support with the ability
to switch to English and potentially other languages.
"""
from typing import Dict


# Translation dictionaries
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    'ar': {
        # General
        'app_name': 'نظام المحاسبة وإدارة الأعمال',
        'app_version': 'الإصدار',
        'save': 'حفظ',
        'cancel': 'إلغاء',
        'delete': 'حذف',
        'edit': 'تعديل',
        'add': 'إضافة',
        'search': 'بحث',
        'close': 'إغلاق',
        'confirm': 'تأكيد',
        'yes': 'نعم',
        'no': 'لا',
        'error': 'خطأ',
        'success': 'تم بنجاح',
        'warning': 'تحذير',
        'info': 'معلومات',
        'loading': 'جاري التحميل...',
        'no_data': 'لا توجد بيانات',
        
        # Login
        'login': 'تسجيل الدخول',
        'logout': 'تسجيل الخروج',
        'username': 'اسم المستخدم',
        'password': 'كلمة المرور',
        'login_title': 'تسجيل الدخول إلى النظام',
        'login_error': 'اسم المستخدم أو كلمة المرور غير صحيحة',
        'login_success': 'تم تسجيل الدخول بنجاح',
        'welcome': 'مرحباً',
        
        # Navigation
        'dashboard': 'لوحة التحكم',
        'pos': 'نقطة البيع',
        'sales': 'المبيعات',
        'purchases': 'المشتريات',
        'inventory': 'المخزون',
        'customers': 'العملاء',
        'suppliers': 'المورّدون',
        'reports': 'التقارير',
        'settings': 'الإعدادات',
        'branches': 'الفروع',
        'users': 'المستخدمون',
        'audit_log': 'سجل التدقيق',
        'backup': 'النسخ الاحتياطي',
        
        # Settings
        'general_settings': 'الإعدادات العامة',
        'organization': 'المنشأة',
        'org_name': 'اسم المنشأة',
        'currency': 'العملة',
        'tax_rate': 'نسبة الضريبة',
        'language': 'اللغة',
        'arabic': 'العربية',
        'english': 'English',
        'display_settings': 'إعدادات العرض',
        'security_settings': 'إعدادات الأمان',
        'backup_settings': 'إعدادات النسخ الاحتياطي',
        'create_backup': 'إنشاء نسخة احتياطية',
        'restore_backup': 'استعادة نسخة احتياطية',
        'backup_created': 'تم إنشاء النسخة الاحتياطية بنجاح',
        'backup_restored': 'تم استعادة النسخة الاحتياطية بنجاح',
        'backup_failed': 'فشل إنشاء النسخة الاحتياطية',
        'restore_failed': 'فشل استعادة النسخة الاحتياطية',
        
        # Users
        'user_management': 'إدارة المستخدمين',
        'create_user': 'إنشاء مستخدم',
        'edit_user': 'تعديل مستخدم',
        'display_name': 'الاسم المعروض',
        'role': 'الدور',
        'status': 'الحالة',
        'active': 'نشط',
        'inactive': 'معطّل',
        'change_password': 'تغيير كلمة المرور',
        'current_password': 'كلمة المرور الحالية',
        'new_password': 'كلمة المرور الجديدة',
        'confirm_password': 'تأكيد كلمة المرور',
        'password_changed': 'تم تغيير كلمة المرور بنجاح',
        
        # Roles
        'role_owner': 'مالك',
        'role_admin': 'مدير النظام',
        'role_manager': 'مدير',
        'role_cashier': 'أمين صندوق',
        'role_accountant': 'محاسب',
        'role_inventory': 'مسؤول مخزون',
        
        # Dashboard
        'today_sales': 'مبيعات اليوم',
        'today_purchases': 'مشتريات اليوم',
        'total_revenue': 'إجمالي الإيرادات',
        'total_expenses': 'إجمالي المصروفات',
        'customer_debts': 'ديون العملاء',
        'supplier_dues': 'مستحقات المورّدين',
        'stock_value': 'قيمة المخزون',
        'low_stock': 'مخزون منخفض',
        'recent_transactions': 'آخر العمليات',
        'sync_status': 'حالة المزامنة',
        
        # Status
        'online': 'متصل',
        'offline': 'غير متصل',
        'syncing': 'جاري المزامنة',
        'sync_error': 'خطأ في المزامنة',
        
        # Audit
        'action': 'الإجراء',
        'user': 'المستخدم',
        'date': 'التاريخ',
        'details': 'التفاصيل',
        'entity': 'الكيان',
        
        # Messages
        'confirm_delete': 'هل أنت متأكد من الحذف؟',
        'cannot_undo': 'لا يمكن التراجع عن هذا الإجراء',
        'saved_successfully': 'تم الحفظ بنجاح',
        'deleted_successfully': 'تم الحذف بنجاح',
        'operation_failed': 'فشلت العملية',
        'no_permission': 'ليس لديك صلاحية لهذا الإجراء',
    },
    
    'en': {
        # General
        'app_name': 'Accounting & Business Management System',
        'app_version': 'Version',
        'save': 'Save',
        'cancel': 'Cancel',
        'delete': 'Delete',
        'edit': 'Edit',
        'add': 'Add',
        'search': 'Search',
        'close': 'Close',
        'confirm': 'Confirm',
        'yes': 'Yes',
        'no': 'No',
        'error': 'Error',
        'success': 'Success',
        'warning': 'Warning',
        'info': 'Information',
        'loading': 'Loading...',
        'no_data': 'No data available',
        
        # Login
        'login': 'Login',
        'logout': 'Logout',
        'username': 'Username',
        'password': 'Password',
        'login_title': 'Login to System',
        'login_error': 'Invalid username or password',
        'login_success': 'Logged in successfully',
        'welcome': 'Welcome',
        
        # Navigation
        'dashboard': 'Dashboard',
        'pos': 'Point of Sale',
        'sales': 'Sales',
        'purchases': 'Purchases',
        'inventory': 'Inventory',
        'customers': 'Customers',
        'suppliers': 'Suppliers',
        'reports': 'Reports',
        'settings': 'Settings',
        'branches': 'Branches',
        'users': 'Users',
        'audit_log': 'Audit Log',
        'backup': 'Backup',
        
        # Settings
        'general_settings': 'General Settings',
        'organization': 'Organization',
        'org_name': 'Organization Name',
        'currency': 'Currency',
        'tax_rate': 'Tax Rate',
        'language': 'Language',
        'arabic': 'العربية',
        'english': 'English',
        'display_settings': 'Display Settings',
        'security_settings': 'Security Settings',
        'backup_settings': 'Backup Settings',
        'create_backup': 'Create Backup',
        'restore_backup': 'Restore Backup',
        'backup_created': 'Backup created successfully',
        'backup_restored': 'Backup restored successfully',
        'backup_failed': 'Backup creation failed',
        'restore_failed': 'Backup restore failed',
        
        # Users
        'user_management': 'User Management',
        'create_user': 'Create User',
        'edit_user': 'Edit User',
        'display_name': 'Display Name',
        'role': 'Role',
        'status': 'Status',
        'active': 'Active',
        'inactive': 'Inactive',
        'change_password': 'Change Password',
        'current_password': 'Current Password',
        'new_password': 'New Password',
        'confirm_password': 'Confirm Password',
        'password_changed': 'Password changed successfully',
        
        # Roles
        'role_owner': 'Owner',
        'role_admin': 'Administrator',
        'role_manager': 'Manager',
        'role_cashier': 'Cashier',
        'role_accountant': 'Accountant',
        'role_inventory': 'Inventory User',
        
        # Dashboard
        'today_sales': "Today's Sales",
        'today_purchases': "Today's Purchases",
        'total_revenue': 'Total Revenue',
        'total_expenses': 'Total Expenses',
        'customer_debts': 'Customer Debts',
        'supplier_dues': 'Supplier Dues',
        'stock_value': 'Stock Value',
        'low_stock': 'Low Stock',
        'recent_transactions': 'Recent Transactions',
        'sync_status': 'Sync Status',
        
        # Status
        'online': 'Online',
        'offline': 'Offline',
        'syncing': 'Syncing',
        'sync_error': 'Sync Error',
        
        # Audit
        'action': 'Action',
        'user': 'User',
        'date': 'Date',
        'details': 'Details',
        'entity': 'Entity',
        
        # Messages
        'confirm_delete': 'Are you sure you want to delete?',
        'cannot_undo': 'This action cannot be undone',
        'saved_successfully': 'Saved successfully',
        'deleted_successfully': 'Deleted successfully',
        'operation_failed': 'Operation failed',
        'no_permission': 'You do not have permission for this action',
    },
}


class I18n:
    """
    Internationalization manager.
    
    Provides translation lookup with language switching support.
    """
    
    _instance = None
    _current_language = 'ar'
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def language(self) -> str:
        """Get current language."""
        return self._current_language
    
    @language.setter
    def language(self, value: str):
        """Set current language."""
        if value in TRANSLATIONS:
            self._current_language = value
    
    def translate(self, key: str) -> str:
        """
        Translate a key to the current language.
        
        Args:
            key: Translation key
            
        Returns:
            Translated string, or the key itself if not found
        """
        translations = TRANSLATIONS.get(self._current_language, {})
        return translations.get(key, key)
    
    def t(self, key: str) -> str:
        """Shortcut for translate()."""
        return self.translate(key)


# Global instance
_i18n = I18n()


def t(key: str) -> str:
    """
    Global translation function.
    
    Args:
        key: Translation key
        
    Returns:
        Translated string
    """
    return _i18n.translate(key)


def set_language(lang: str):
    """Set the global language."""
    _i18n.language = lang


def get_language() -> str:
    """Get the current global language."""
    return _i18n.language
