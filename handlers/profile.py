from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold, hcode

from database.methods import get_or_create_user, get_user_balance, get_user_purchases
from keyboards.keyboards import get_profile_keyboard, get_main_keyboard, get_balance_keyboard


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
        f"👤 {hbold('Ваш профиль')}\n\n"
        f"Имя: {user.first_name or 'Не указано'} {user.last_name or ''}\n"
        f"Имя пользователя: @{user.username or 'Не указано'}\n"
        f"Баланс: {hbold(f'{balance:.2f}')} монет\n"
        f"Аккаунт создан: {user.created_at.strftime('%Y-%m-%d')}\n"
    )

    await message.answer(profile_text, reply_markup=get_profile_keyboard())


async def show_purchases(message: Message):
    """Show user's purchases"""
    # Get user purchases
    purchases = await get_user_purchases(message.from_user.id)

    if not purchases:
        await message.answer(
            "Вы еще не совершали покупок. Проверьте наш каталог!",
            reply_markup=get_main_keyboard(message.from_user.id)
        )
        return

    # Format purchases message
    purchases_text = f"🛍 {hbold('Ваши покупки')}\n\n"

    for i, purchase in enumerate(purchases, 1):
        purchases_text += (
            f"{i}. {hbold(purchase['title'])}\n"
            f"   Цена: {hcode(f'{purchase['purchase_price']:.2f}')} монет\n"
            f"   Дата: {purchase['purchase_date'].strftime('%Y-%m-%d %H:%M')}\n\n"
        )

    await message.answer(purchases_text, reply_markup=get_main_keyboard(message.from_user.id))


async def show_balance(message: Message):
    """Show user's balance"""
    # Get user balance
    balance = await get_user_balance(message.from_user.id)

    balance_text = (
        f"💰 {hbold('Ваш баланс')}\n\n"
        f"Текущий баланс: {hbold(f'{balance:.2f}')} монет\n\n"
        f"Вы можете использовать свой баланс для покупки товаров из нашего каталога или пополнить его, чтобы добавить больше монет."
    )

    # Make sure we're using the correct keyboard with the top-up button
    await message.answer(balance_text, reply_markup=get_balance_keyboard())


def register_profile_handlers(dp: Dispatcher):
    """Register profile handlers"""
    dp.message.register(cmd_profile, Command("profile"))
    dp.message.register(cmd_profile, F.text == "👤 Профиль")
    dp.message.register(show_purchases, F.text == "🛍 Мои покупки")
    dp.message.register(show_balance, F.text == "💰 Баланс")
    dp.message.register(show_balance, Command("balance"))