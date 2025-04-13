import logging
import json
import requests
import random
import string
from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold, hcode
from aiogram.fsm.context import FSMContext

from config import load_config
from database.methods import get_user_balance, update_user_balance
from keyboards.keyboards import (
    get_balance_topup_keyboard,
    get_payment_methods_keyboard,
    get_payment_confirmation_keyboard,
    get_main_keyboard,
    get_payment_link_keyboard
)
from states.states import PaymentState

# Load configuration
config = load_config()

# Configure logging
logger = logging.getLogger(__name__)

# Define coin packages
COIN_PACKAGES = {
    "500": {"coins": 500, "price_usd": 5},
    "1000": {"coins": 1000, "price_usd": 10},
    "3000": {"coins": 3000, "price_usd": 30},
    "10000": {"coins": 10000, "price_usd": 100}
}

# Define payment methods
PAYMENT_METHODS = {
    "cryptocloud": "CryptoCloud",
    "wata": "Wata",
    "payeer": "Payeer",
    "b2pay": "B2Pay"
}


async def cmd_topup(message: Message):
    """Handle /topup command"""
    # Get user balance
    balance = await get_user_balance(message.from_user.id)

    # Format message
    topup_text = (
        f"💰 {hbold('Пополнение баланса')}\n\n"
        f"Текущий баланс: {hbold(f'{balance:.2f}')} монет\n\n"
        f"Выберите количество монет, которое вы хотите купить:"
    )

    await message.answer(
        topup_text,
        reply_markup=get_balance_topup_keyboard()
    )


async def show_topup(callback: CallbackQuery):
    """Show balance top-up options when the 'Top Up Balance' button is clicked"""
    # Get user balance
    balance = await get_user_balance(callback.from_user.id)

    # Format message
    topup_text = (
        f"💰 {hbold('Пополнение баланса')}\n\n"
        f"Текущий баланс: {hbold(f'{balance:.2f}')} монет\n\n"
        f"Выберите количество монет, которое вы хотите купить:"
    )

    await callback.message.answer(
        topup_text,
        reply_markup=get_balance_topup_keyboard()
    )
    await callback.answer()


async def select_payment_amount(callback: CallbackQuery, state: FSMContext):
    """Handle selected coin package"""
    # Extract package code from callback data (e.g., "topup:500")
    package_code = callback.data.split(':')[1]

    if package_code not in COIN_PACKAGES:
        await callback.answer("Неверный пакет. Пожалуйста, выберите снова.", show_alert=True)
        return

    package = COIN_PACKAGES[package_code]

    # Save package info to state
    await state.update_data(
        coin_amount=package["coins"],
        price_usd=package["price_usd"]
    )

    # Move to payment method selection
    await state.set_state(PaymentState.select_method)

    # Format message
    payment_text = (
        f"💰 {hbold('Выберите способ оплаты')}\n\n"
        f"Пакет: {hbold(f'{package["coins"]}')} монет\n"
        f"Цена: {hcode(f'${package["price_usd"]:.2f}')}\n\n"
        f"Пожалуйста, выберите предпочитаемый способ оплаты:"
    )

    await callback.message.answer(
        payment_text,
        reply_markup=get_payment_methods_keyboard()
    )
    await callback.answer()


async def select_payment_method(callback: CallbackQuery, state: FSMContext):
    """Handle selected payment method"""
    # Extract method from callback data (e.g., "payment_method:cryptocloud")
    method_code = callback.data.split(':')[1]

    if method_code not in PAYMENT_METHODS:
        await callback.answer("Неверный способ оплаты. Пожалуйста, выберите снова.", show_alert=True)
        return

    # Add method to state
    state_data = await state.get_data()
    await state.update_data(
        payment_method=method_code,
        payment_method_name=PAYMENT_METHODS[method_code]
    )

    coin_amount = state_data.get("coin_amount")
    price_usd = state_data.get("price_usd")

    # Format confirmation message
    confirmation_text = (
        f"💰 {hbold('Подтверждение оплаты')}\n\n"
        f"Пакет: {hbold(f'{coin_amount}')} монет\n"
        f"Цена: {hcode(f'${price_usd:.2f}')}\n"
        f"Способ оплаты: {hbold(PAYMENT_METHODS[method_code])}\n\n"
        f"Нажмите кнопку ниже, чтобы перейти к оплате."
    )

    await callback.message.answer(
        confirmation_text,
        reply_markup=get_payment_confirmation_keyboard()
    )
    await callback.answer()


async def generate_cryptocloud_invoice(amount, user_id, coin_amount):
    """Generate a payment invoice via CryptoCloud API"""
    url = "https://api.cryptocloud.plus/v2/invoice/create"

    headers = {
        "Authorization": f"Token {config.cryptocloud_api_key}",
        "Content-Type": "application/json"
    }

    # Generate random 8-character hash
    hash_part = ''.join(random.choices(string.digits, k=8))

    # Create order_id with format tg_telegramID_hash
    # More explicit format to ensure we can identify it in webhooks
    order_id = f"tg_{user_id}_{hash_part}"

    # Add information about the coin amount to add_fields
    add_fields = {
        "user_id": str(user_id),
        "coin_amount": str(coin_amount),
        "email": f"user{user_id}@example.com"  # Placeholder email
    }

    data = {
        "amount": amount,
        "shop_id": config.cryptocloud_shop_id,
        "currency": "USD",
        "order_id": order_id,  # Set order_id at the root level
        "add_fields": add_fields
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        logger.info(f"CryptoCloud API request: {data}")

        if response.status_code == 200:
            result = response.json()
            logger.info(f"CryptoCloud API response: {result}")

            if result.get("status") == "success":
                logger.info(
                    f"Created CryptoCloud invoice for user {user_id}, amount: {amount}, coins: {coin_amount}, order_id: {order_id}")
                # Return the payment link generated by CryptoCloud
                return result["result"]["link"]

        logger.error(f"CryptoCloud API error: {response.status_code} - {response.text}")
        return None
    except Exception as e:
        logger.error(f"Error generating CryptoCloud invoice: {e}")
        return None


async def process_payment(callback: CallbackQuery, state: FSMContext):
    """Process payment request"""
    # Get payment data
    payment_data = await state.get_data()
    payment_method = payment_data.get('payment_method')
    coin_amount = payment_data.get('coin_amount')
    price_usd = payment_data.get('price_usd')

    payment_link = None

    # Generate payment link based on the selected method
    if payment_method == "cryptocloud":
        payment_link = await generate_cryptocloud_invoice(price_usd, callback.from_user.id, coin_amount)
    elif payment_method in ["wata", "payeer", "b2pay"]:
        # Placeholder for other payment methods
        payment_link = f"https://example.com/placeholder-payment/{payment_method}/{price_usd}"

    if payment_link:
        # Success message with payment link
        success_text = (
            f"🔗 {hbold('Ссылка на оплату создана')}\n\n"
            f"Пакет: {hbold(f'{coin_amount}')} монет\n"
            f"Цена: {hcode(f'${price_usd:.2f}')}\n"
            f"Способ оплаты: {hbold(payment_data.get('payment_method_name'))}\n\n"
            f"Нажмите кнопку ниже, чтобы перейти на страницу оплаты. После успешной оплаты монеты будут автоматически зачислены на ваш баланс.\n\n"
            f"Вы можете проверить статус оплаты с помощью команды /check_payment."
        )

        await callback.message.answer(
            success_text,
            reply_markup=get_payment_link_keyboard(payment_link)
        )
    else:
        # If payment link generation failed
        error_text = (
            f"❌ {hbold('Ошибка оплаты')}\n\n"
            f"Мы не смогли создать ссылку на оплату в данный момент. Пожалуйста, попробуйте позже или выберите другой способ оплаты."
        )

        await callback.message.answer(
            error_text,
            reply_markup=get_balance_topup_keyboard()
        )

    # Clear state
    await state.clear()
    await callback.answer()


async def check_payment_status(message: Message):
    """Handle /check_payment command to check on recent payments"""
    user_id = message.from_user.id
    balance = await get_user_balance(user_id)

    # This is a simple implementation - in a real system, you might
    # want to check the actual payment status from CryptoCloud API

    await message.answer(
        f"💰 <b>Статус оплаты</b>\n\n"
        f"Ваш текущий баланс: <b>{balance:.2f}</b> монет\n\n"
        f"Если вы недавно сделали платеж, пожалуйста, подождите несколько минут для его обработки. "
        f"Ваш баланс будет обновлен автоматически, когда платеж будет подтвержден.\n\n"
        f"Если у вас возникли проблемы с оплатой, пожалуйста, обратитесь в службу поддержки.",
        reply_markup=get_main_keyboard(user_id)
    )


async def cancel_payment(callback: CallbackQuery, state: FSMContext):
    """Cancel payment process"""
    await callback.message.answer(
        "Оплата отменена. С вас не списаны средства.",
        reply_markup=get_main_keyboard(callback.from_user.id)
    )

    # Clear state
    await state.clear()
    await callback.answer()


def register_payment_handlers(dp: Dispatcher):
    """Register payment handlers"""
    dp.message.register(cmd_topup, Command("topup"))
    dp.message.register(check_payment_status, Command("check_payment"))
    dp.callback_query.register(show_topup, F.data == "topup_balance")
    dp.callback_query.register(select_payment_amount, F.data.startswith("topup:"))
    dp.callback_query.register(select_payment_method, F.data.startswith("payment_method:"))
    dp.callback_query.register(process_payment, F.data == "confirm_payment")
    dp.callback_query.register(cancel_payment, F.data == "cancel_payment")