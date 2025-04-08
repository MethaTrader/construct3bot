from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold, hcode
from datetime import datetime, timedelta

from config import load_config
from database.methods import (
    get_total_users_count,
    get_new_users_count,
    get_active_users_count,
    get_all_products,
    get_total_purchases_count,
    get_recent_purchases_data
)
from keyboards.keyboards import get_admin_keyboard

# Load config to get admin IDs
config = load_config()
ADMIN_IDS = config.admin_ids

async def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS

async def show_statistics(callback: CallbackQuery):
    """Show bot statistics for admin"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return
    
    # Calculate dates
    now = datetime.utcnow()
    day_ago = now - timedelta(days=1)
    two_weeks_ago = now - timedelta(days=14)
    
    # Get statistics data
    total_users = await get_total_users_count()
    new_users_24h = await get_new_users_count(day_ago)
    active_users = await get_active_users_count(two_weeks_ago)
    
    # Get product data
    all_products = await get_all_products(available_only=False)
    available_products = await get_all_products(available_only=True)
    
    # Get purchase data
    total_purchases = await get_total_purchases_count()
    recent_purchases_data = await get_recent_purchases_data(two_weeks_ago)
    recent_purchases_count = len(recent_purchases_data)
    recent_purchases_amount = sum(purchase['purchase_price'] for purchase in recent_purchases_data)
    
    # Format the statistics message
    stats_message = (
        f"📊 {hbold('Bot Statistics')}\n\n"
        f"👥 {hbold('User Statistics:')}\n"
        f"• Total users: {hcode(str(total_users))}\n"
        f"• New users (24h): {hcode(str(new_users_24h))}\n"
        f"• Active users (14d): {hcode(str(active_users))}\n\n"
        
        f"🏪 {hbold('Product Statistics:')}\n"
        f"• Products: {hcode(f'{len(available_products)}/{len(all_products)}')}\n\n"
        
        f"💰 {hbold('Sales Statistics:')}\n"
        f"• Total sales: {hcode(str(total_purchases))}\n"
        f"• Recent sales (14d): {hcode(str(recent_purchases_count))}\n"
        f"• Recent revenue (14d): {hcode(f'{recent_purchases_amount:.2f}')} coins\n\n"
        
        f"Generated at: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC"
    )
    
    await callback.message.answer(
        stats_message,
        reply_markup=get_admin_keyboard()
    )
    await callback.answer()

def register_statistics_handlers(dp: Dispatcher):
    """Register statistics handlers"""
    dp.callback_query.register(show_statistics, F.data == "admin_statistics")