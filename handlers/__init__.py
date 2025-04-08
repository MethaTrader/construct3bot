from aiogram import Dispatcher
from handlers.user import register_user_handlers
from handlers.catalog import register_catalog_handlers
from handlers.purchases import register_purchase_handlers
from handlers.profile import register_profile_handlers
from handlers.admin import register_admin_handlers
from handlers.cart import register_cart_handlers
from handlers.statistics import register_statistics_handlers
from handlers.payment import register_payment_handlers

def register_handlers(dp: Dispatcher):
    """Register all handlers"""
    # Register user handlers
    register_user_handlers(dp)
    
    # Register catalog handlers
    register_catalog_handlers(dp)
    
    # Register purchase handlers
    register_purchase_handlers(dp)
    
    # Register profile handlers
    register_profile_handlers(dp)
    
    # Register admin handlers
    register_admin_handlers(dp)
    
    # Register cart handlers
    register_cart_handlers(dp)
    
    # Register statistics handlers
    register_statistics_handlers(dp)
    
    # Register payment handlers
    register_payment_handlers(dp)