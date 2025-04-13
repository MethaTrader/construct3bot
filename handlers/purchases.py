from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold, hcode
from aiogram.fsm.context import FSMContext

from database.methods import create_purchase, get_product, get_user_balance
from keyboards.keyboards import get_purchase_confirmation_keyboard, get_main_keyboard


async def buy_product(callback: CallbackQuery, state: FSMContext):
    """Handle product purchase request"""
    # Extract product ID from callback data (buy_product:123)
    product_id = int(callback.data.split(':')[1])

    # Get product details
    product = await get_product(product_id)

    if not product or not product.available:
        await callback.answer("Этот товар больше недоступен.", show_alert=True)
        return

    # Get user balance
    balance = await get_user_balance(callback.from_user.id)

    if balance < product.price:
        await callback.answer(
            "Недостаточно средств. Пожалуйста, пополните баланс.",
            show_alert=True
        )
        return

    # Store product info in state
    await state.update_data(product_id=product_id, product_price=product.price)

    # Show confirmation message
    confirmation_text = (
        f"🛒 {hbold('Подтверждение покупки')}\n\n"
        f"Товар: {hbold(product.title)}\n"
        f"Цена: {hcode(f'{product.price:.2f}')} монет\n"
        f"Ваш баланс: {hcode(f'{balance:.2f}')} монет\n\n"
        f"После покупки: {hcode(f'{balance - product.price:.2f}')} монет\n\n"
        f"Хотите продолжить покупку?"
    )

    await callback.message.answer(
        confirmation_text,
        reply_markup=get_purchase_confirmation_keyboard(product_id)
    )
    await callback.answer()


async def confirm_purchase(callback: CallbackQuery, state: FSMContext):
    """Handle purchase confirmation"""
    # Extract product ID from callback data (confirm_purchase:123)
    product_id = int(callback.data.split(':')[1])

    # Get product details
    product = await get_product(product_id)

    if not product or not product.available:
        await callback.answer("Этот товар больше недоступен.", show_alert=True)
        return

    # Process the purchase
    purchase = await create_purchase(
        callback.from_user.id,
        product_id,
        product.price
    )

    if not purchase:
        await callback.answer("Покупка не удалась. Пожалуйста, проверьте свой баланс.", show_alert=True)
        return

    # Send success message
    success_text = (
        f"✅ {hbold('Покупка успешна')}\n\n"
        f"Вы успешно приобрели {hbold(product.title)}.\n\n"
        f"Вы можете найти вашу покупку в разделе 'Мои покупки'."
    )

    # If the product has a file, send it
    if product.file_id:
        await callback.message.answer(success_text)

        # Send the file with a caption
        await callback.message.answer_document(
            document=product.file_id,
            caption=f"Вот ваша покупка: {product.title}"
        )
    else:
        await callback.message.answer(success_text, reply_markup=get_main_keyboard())

    await callback.answer("Покупка успешна!")

    # Clear state
    await state.clear()


async def cancel_purchase(callback: CallbackQuery, state: FSMContext):
    """Handle purchase cancellation"""
    await callback.message.answer(
        "Покупка отменена. С вас не списали средства.",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()

    # Clear state
    await state.clear()


def register_purchase_handlers(dp: Dispatcher):
    """Register purchase handlers"""
    dp.callback_query.register(buy_product, F.data.startswith("buy_product:"))
    dp.callback_query.register(confirm_purchase, F.data.startswith("confirm_purchase:"))
    dp.callback_query.register(cancel_purchase, F.data == "cancel_purchase")