from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold, hcode

from database.methods import get_user_purchases
from keyboards.keyboards import get_main_keyboard

async def cmd_cart(message: Message):
    """Handle /cart command and Cart button"""
    # Redirect to purchases (since we don't have a traditional cart)
    purchases = await get_user_purchases(message.from_user.id)
    
    if not purchases:
        await message.answer(
            "Your cart is empty. Browse our catalog to find products!",
            reply_markup=get_main_keyboard(message.from_user.id)
        )
        return
    
    # Format purchases message
    purchases_text = f"🛒 {hbold('Your Cart')}\n\n"
    purchases_text += "Here are your past purchases:\n\n"
    
    for i, purchase in enumerate(purchases, 1):
        purchases_text += (
            f"{i}. {hbold(purchase['title'])}\n"
            f"   Price: {hcode(f'{purchase['purchase_price']:.2f}')} coins\n"
            f"   Date: {purchase['purchase_date'].strftime('%Y-%m-%d %H:%M')}\n\n"
        )
    
    await message.answer(purchases_text, reply_markup=get_main_keyboard(message.from_user.id))

def register_cart_handlers(dp: Dispatcher):
    """Register cart handlers"""
    dp.message.register(cmd_cart, Command("cart"))
    dp.message.register(cmd_cart, F.text == "🛒 Cart")