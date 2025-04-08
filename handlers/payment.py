from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold, hcode
from aiogram.fsm.context import FSMContext

from config import load_config
from database.methods import get_user_balance
from keyboards.keyboards import (
    get_balance_topup_keyboard,
    get_payment_methods_keyboard,
    get_payment_confirmation_keyboard,
    get_main_keyboard
)
from states.states import PaymentState

# Define coin packages
COIN_PACKAGES = {
    "500": {"coins": 500, "price_usd": 25},
    "1000": {"coins": 1000, "price_usd": 50},
    "3000": {"coins": 3000, "price_usd": 150},
    "10000": {"coins": 10000, "price_usd": 500}
}

# Define payment methods
PAYMENT_METHODS = {
    "cryptomus": "Cryptomus",
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
        f"💰 {hbold('Balance Top-Up')}\n\n"
        f"Current balance: {hbold(f'{balance:.2f}')} coins\n\n"
        f"Choose the amount of coins you want to purchase:"
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
        f"💰 {hbold('Balance Top-Up')}\n\n"
        f"Current balance: {hbold(f'{balance:.2f}')} coins\n\n"
        f"Choose the amount of coins you want to purchase:"
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
        await callback.answer("Invalid package. Please select again.", show_alert=True)
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
        f"💰 {hbold('Select Payment Method')}\n\n"
        f"Package: {hbold(f'{package["coins"]}')} coins\n"
        f"Price: {hcode(f'${package["price_usd"]:.2f}')}\n\n"
        f"Please select your preferred payment method:"
    )
    
    await callback.message.answer(
        payment_text,
        reply_markup=get_payment_methods_keyboard()
    )
    await callback.answer()

async def select_payment_method(callback: CallbackQuery, state: FSMContext):
    """Handle selected payment method"""
    # Extract method from callback data (e.g., "payment_method:cryptomus")
    method_code = callback.data.split(':')[1]
    
    if method_code not in PAYMENT_METHODS:
        await callback.answer("Invalid payment method. Please select again.", show_alert=True)
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
        f"💰 {hbold('Confirm Payment')}\n\n"
        f"Package: {hbold(f'{coin_amount}')} coins\n"
        f"Price: {hcode(f'${price_usd:.2f}')}\n"
        f"Payment method: {hbold(PAYMENT_METHODS[method_code])}\n\n"
        f"Click the button below to proceed to payment."
    )
    
    await callback.message.answer(
        confirmation_text,
        reply_markup=get_payment_confirmation_keyboard()
    )
    await callback.answer()

async def process_payment(callback: CallbackQuery, state: FSMContext):
    """Process payment request"""
    # Get payment data
    payment_data = await state.get_data()
    
    # For demonstration, just show a success message
    # In a real scenario, this would redirect to the payment provider
    
    success_text = (
        f"🔗 {hbold('Payment Link Generated')}\n\n"
        f"Package: {hbold(f'{payment_data.get('coin_amount')}')} coins\n"
        f"Price: {hcode(f'${payment_data.get('price_usd'):.2f}')}\n"
        f"Payment method: {hbold(payment_data.get('payment_method_name'))}\n\n"
        f"In a real implementation, you would be redirected to the payment provider.\n"
        f"After successful payment, the coins would be credited to your balance."
    )
    
    await callback.message.answer(
        success_text,
        reply_markup=get_main_keyboard(callback.from_user.id)
    )
    
    # Clear state
    await state.clear()
    await callback.answer()

async def cancel_payment(callback: CallbackQuery, state: FSMContext):
    """Cancel payment process"""
    await callback.message.answer(
        "Payment cancelled. You were not charged.",
        reply_markup=get_main_keyboard(callback.from_user.id)
    )
    
    # Clear state
    await state.clear()
    await callback.answer()

def register_payment_handlers(dp: Dispatcher):
    """Register payment handlers"""
    dp.message.register(cmd_topup, Command("topup"))
    dp.callback_query.register(show_topup, F.data == "topup_balance")
    dp.callback_query.register(select_payment_amount, F.data.startswith("topup:"))
    dp.callback_query.register(select_payment_method, F.data.startswith("payment_method:"))
    dp.callback_query.register(process_payment, F.data == "confirm_payment")
    dp.callback_query.register(cancel_payment, F.data == "cancel_payment")