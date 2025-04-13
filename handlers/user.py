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
        f"Привет, {hbold(message.from_user.first_name)}! 👋\n\n"
        f"Добро пожаловать в наш магазин! Здесь вы можете:\n"
        f"• Просматривать каталог товаров 📚\n"
        f"• Покупать цифровые товары 💸\n"
        f"• Скачивать свои покупки 📁\n\n"
        f"Используйте меню ниже, чтобы начать!"
    )

    # Send welcome message with main keyboard (including admin button if user is admin)
    await message.answer(welcome_text, reply_markup=get_main_keyboard(message.from_user.id))


async def cmd_help(message: Message):
    """Handle /help command"""
    help_text = (
        f"📚 {hbold('Помощь и команды')}:\n\n"
        f"/start - Запустить бота\n"
        f"/help - Показать это сообщение помощи\n"
        f"/catalog - Просмотреть наши товары\n"
        f"/profile - Просмотреть свой профиль\n"
        f"/balance - Проверить свой баланс\n"
        f"/purchases - Просмотреть свои покупки\n"
        f"/support - Связаться с поддержкой\n"
    )

    # Add admin commands if user is admin
    if message.from_user.id in ADMIN_IDS:
        help_text += (
            f"\n{hbold('✅ Команды администратора')}:\n"
            f"/admin - Доступ к панели администратора\n"
        )

    help_text += "\nЕсли у вас есть вопросы или проблемы, не стесняйтесь обращаться в нашу службу поддержки!"

    await message.answer(help_text)


async def cmd_purchases(message: Message):
    """Handle /purchases command"""
    await show_purchases(message)


async def cmd_support(message: Message):
    """Handle /support command and Support button"""
    support_text = (
        f"📞 {hbold('Центр поддержки')}\n\n"
        f"Нужна помощь? Мы здесь для вас! Свяжитесь с нами по вопросам:\n\n"
        f"🤖 {hbold('Вопросы по боту')}\n"
        f"Любые вопросы по использованию бота и его функций\n\n"
        f"💻 {hbold('Вопросы по исходному коду')}\n"
        f"Технические вопросы по реализации бота\n\n"
        f"🛒 {hbold('Покупка исходного кода')}\n"
        f"Интересуетесь получением собственной версии этого бота\n\n"
        f"💰 {hbold('Проблемы с оплатой')}\n"
        f"Проблемы с платежами или пополнением баланса\n\n"
        f"❓ {hbold('Другие вопросы')}\n"
        f"Любые другие запросы, не указанные выше\n\n"
        f"Свяжитесь с нашей службой поддержки, нажав на кнопку ниже:"
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
            "Главное меню:",
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
    dp.message.register(cmd_support, F.text == "📞 Поддержка")
    dp.message.register(handle_admin_button, F.text == "👑 Панель администратора")

    # Inline button handlers
    dp.callback_query.register(handle_inline_buttons, F.data.in_([
        "back_to_menu", "my_purchases", "show_balance",
        "open_catalog", "back_to_categories"
    ]))