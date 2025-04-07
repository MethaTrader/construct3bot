from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold, hcode

from database.methods import get_or_create_user, get_user_balance, get_user_purchases
from keyboards.keyboards import get_profile_keyboard, get_main_keyboard

async def cmd_profile(message: Message):
    """Handle /profile command"""
    # Get or create user
    user = await get_or_create_user(message.from_user.id, {
        'username': message.from_user.username,
        'first_name': message.from_user.first_name,
        'last_name': message.from_user.last_name
    })
    
    # Get the latest balance directly using the balance method
    balance = await get_user_balance(message.from_user.id)
    
    # Format profile message
    profile_text = (
        f"👤 {hbold('Your Profile')}\n\n"
        f"Name: {user.first_name or 'Not set'} {user.last_name or ''}\n"
        f"Username: @{user.username or 'Not set'}\n"
        f"Balance: {hbold(f'{balance:.2f}')} coins\n"
        f"Account created: {user.created_at.strftime('%Y-%m-%d')}\n"
    )
    
    await message.answer(profile_text, reply_markup=get_profile_keyboard())

async def show_purchases(message: Message):
    """Show user's purchases"""
    # Get user purchases
    purchases = await get_user_purchases(message.from_user.id)
    
    if not purchases:
        await message.answer(
            "You haven't made any purchases yet. Check our catalog!",
            reply_markup=get_main_keyboard(message.from_user.id)
        )
        return
    
    # Format purchases message
    purchases_text = f"🛍 {hbold('Your Purchases')}\n\n"
    
    for i, purchase in enumerate(purchases, 1):
        purchases_text += (
            f"{i}. {hbold(purchase['title'])}\n"
            f"   Price: {hcode(f'{purchase['purchase_price']:.2f}')} coins\n"
            f"   Date: {purchase['purchase_date'].strftime('%Y-%m-%d %H:%M')}\n\n"
        )
    
    await message.answer(purchases_text, reply_markup=get_main_keyboard(message.from_user.id))

async def show_balance(message: Message):
    """Show user's balance"""
    # Get user balance
    balance = await get_user_balance(message.from_user.id)
    
    balance_text = (
        f"💰 {hbold('Your Balance')}\n\n"
        f"Current balance: {hbold(f'{balance:.2f}')} coins\n\n"
        f"You can use your balance to purchase products from our catalog."
    )
    
    await message.answer(balance_text, reply_markup=get_main_keyboard(message.from_user.id))

def register_profile_handlers(dp: Dispatcher):
    """Register profile handlers"""
    dp.message.register(cmd_profile, Command("profile"))
    dp.message.register(cmd_profile, F.text == "👤 Profile")
    dp.message.register(show_purchases, F.text == "🛍 My Purchases")
    dp.message.register(show_balance, F.text == "💰 Balance")
    dp.message.register(show_balance, Command("balance"))