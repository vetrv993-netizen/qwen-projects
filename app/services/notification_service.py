"""
Notification service - manages application notifications.
"""
import logging
from typing import List, Dict, Any
from datetime import datetime

from app.database.connection import DatabaseManager
from app.repositories.product_repo import ProductRepository


logger = logging.getLogger(__name__)


class NotificationService:
    """Manages application notifications."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.product_repo = ProductRepository(db)
    
    def get_notifications(self) -> List[Dict[str, Any]]:
        """Get all current notifications."""
        notifications = []
        
        # Low stock alerts
        low_stock = self.product_repo.get_low_stock(limit=5)
        for product in low_stock:
            notifications.append({
                'type': 'warning',
                'icon': '⚠️',
                'title': 'مخزون منخفض',
                'message': f"{product['name_ar']} - الكمية: {product['stock_quantity']}",
                'time': datetime.now().isoformat(),
            })
        
        # Expiring products
        expiring = self.product_repo.get_expiring(days=30, limit=5)
        for product in expiring:
            notifications.append({
                'type': 'danger',
                'icon': '🔴',
                'title': 'منتج قريب الانتهاء',
                'message': f"{product['name_ar']} - ينتهي: {product['expiry_date']}",
                'time': datetime.now().isoformat(),
            })
        
        return notifications
    
    def get_notification_count(self) -> int:
        """Get total notification count."""
        low_stock = self.product_repo.get_low_stock(limit=100)
        expiring = self.product_repo.get_expiring(days=30, limit=100)
        return len(low_stock) + len(expiring)
