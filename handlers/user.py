from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold
from datetime import datetime

from database.methods import get_or_create_user, get_user_purchases
from keyboards.keyboards import get_main_keyboard, get_profile_keyboard
from handlers.catalog import cmd_catalog
from handlers.profile import show_purchases, show_balance

async def cmd_start(message: Message):
    """Handle /start command"""
    # Get user data for the database
    user_data = {
        'username': message.from_user.username,
        'first_name': message.from_user.first_name,
        'last_name': message.from_user.last_name
    }
    
    # Save or update user in the database
    user = await get_or_create_user(message.from_user.id, user_data)
    
    # Welcome message
    welcome_text = (
        f"Hello, {hbold(message.from_user.first_name)}! 👋\n\n"
        f"Welcome to our Online Store Bot! Here you can:\n"
        f"• Browse our product catalog 📚\n"
        f"• Purchase digital products 💸\n"
        f"• Download your purchases 📁\n\n"
        f"Use the menu below to get started!"
    )
    
    # Send welcome message with main keyboard
    await message.answer(welcome_text, reply_markup=get_main_keyboard())

async def cmd_help(message: Message):
    """Handle /help command"""
    help_text = (
        f"📚 {hbold('Help & Commands')}:\n\n"
        f"/start - Start the bot\n"
        f"/help - Show this help message\n"
        f"/catalog - Browse our products\n"
        f"/profile - View your profile\n"
        f"/balance - Check your balance\n"
        f"/purchases - View your purchases\n\n"
        f"If you have any questions or issues, feel free to contact our support!"
    )
    
    await message.answer(help_text)

async def cmd_purchases(message: Message):
    """Handle /purchases command"""
    await show_purchases(message)

async def handle_inline_buttons(callback: CallbackQuery):
    """Handle common inline keyboard buttons"""
    action = callback.data
    
    if action == "back_to_menu":
        await callback.message.answer(
            "Main menu:", 
            reply_markup=get_main_keyboard()
        )
    elif action == "my_purchases":
        await show_purchases(callback.message)
    elif action == "show_balance":
        await show_balance(callback.message)
    elif action == "open_catalog":
        await cmd_catalog(callback.message)
    elif action == "back_to_categories":
        await cmd_catalog(callback.message)
    
    await callback.answer()

def register_user_handlers(dp: Dispatcher):
    """Register user handlers"""
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_help, Command("help"))
    dp.message.register(cmd_purchases, Command("purchases"))
    
    # Inline button handlers
    dp.callback_query.register(handle_inline_buttons, F.data.in_([
        "back_to_menu", "my_purchases", "show_balance", 
        "open_catalog", "back_to_categories"
    ]))