from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold
from datetime import datetime

from config import load_config
from database.methods import get_or_create_user, get_user_purchases
from keyboards.keyboards import get_main_keyboard, get_profile_keyboard, get_support_keyboard
from handlers.catalog import cmd_catalog
from handlers.profile import show_purchases, show_balance
from handlers.admin import cmd_admin

# Load config to get admin IDs and contact
config = load_config()
ADMIN_IDS = config.admin_ids
ADMIN_CONTACT = config.admin_contact

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
    
    # Send welcome message with main keyboard (including admin button if user is admin)
    await message.answer(welcome_text, reply_markup=get_main_keyboard(message.from_user.id))

async def cmd_help(message: Message):
    """Handle /help command"""
    help_text = (
        f"📚 {hbold('Help & Commands')}:\n\n"
        f"/start - Start the bot\n"
        f"/help - Show this help message\n"
        f"/catalog - Browse our products\n"
        f"/profile - View your profile\n"
        f"/balance - Check your balance\n"
        f"/purchases - View your purchases\n"
        f"/support - Contact support\n"
    )
    
    # Add admin commands if user is admin
    if message.from_user.id in ADMIN_IDS:
        help_text += (
            f"\n{hbold('✅ Admin Commands')}:\n"
            f"/admin - Access admin panel\n"
        )
    
    help_text += "\nIf you have any questions or issues, feel free to contact our support!"
    
    await message.answer(help_text)

async def cmd_purchases(message: Message):
    """Handle /purchases command"""
    await show_purchases(message)

async def cmd_support(message: Message):
    """Handle /support command and Support button"""
    support_text = (
        f"📞 {hbold('Support Center')}\n\n"
        f"Need help? We're here for you! Contact us for:\n\n"
        f"🤖 {hbold('Bot Questions')}\n"
        f"Any questions about using the bot and its features\n\n"
        f"💻 {hbold('Source Code Questions')}\n"
        f"Technical questions about the bot's implementation\n\n"
        f"🛒 {hbold('Purchase Source Code')}\n"
        f"Interested in getting your own version of this bot\n\n"
        f"💰 {hbold('Payment Issues')}\n"
        f"Problems with payments or balance top-ups\n\n"
        f"❓ {hbold('Other Questions')}\n"
        f"Any other inquiries not covered above\n\n"
        f"Contact our support team by clicking the button below:"
    )
    
    await message.answer(
        support_text,
        reply_markup=get_support_keyboard(ADMIN_CONTACT)
    )

async def handle_inline_buttons(callback: CallbackQuery):
    """Handle common inline keyboard buttons"""
    action = callback.data
    
    if action == "back_to_menu":
        await callback.message.answer(
            "Main menu:", 
            reply_markup=get_main_keyboard(callback.from_user.id)
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

async def handle_admin_button(message: Message):
    """Handle the Admin Panel button"""
    await cmd_admin(message)

def register_user_handlers(dp: Dispatcher):
    """Register user handlers"""
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_help, Command("help"))
    dp.message.register(cmd_purchases, Command("purchases"))
    dp.message.register(cmd_support, Command("support"))
    dp.message.register(cmd_support, F.text == "📞 Support")
    dp.message.register(handle_admin_button, F.text == "👑 Admin Panel")
    
    # Inline button handlers
    dp.callback_query.register(handle_inline_buttons, F.data.in_([
        "back_to_menu", "my_purchases", "show_balance", 
        "open_catalog", "back_to_categories"
    ]))