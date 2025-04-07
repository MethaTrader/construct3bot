from aiogram import Dispatcher
from handlers.user import register_user_handlers
from handlers.catalog import register_catalog_handlers
from handlers.purchases import register_purchase_handlers
from handlers.profile import register_profile_handlers

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