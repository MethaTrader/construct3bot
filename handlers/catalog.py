from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold, hcode
import math

from database.methods import get_all_categories, get_products_by_category, get_all_products, get_product
from keyboards.keyboards import (
    get_categories_keyboard,
    get_products_keyboard,
    get_product_details_keyboard,
    get_main_keyboard,
    get_paginated_products_keyboard
)

# Set the number of products per page
PRODUCTS_PER_PAGE = 3


async def cmd_catalog(message: Message):
    """Handle /catalog command"""
    # Get all categories
    categories = await get_all_categories()

    # Get all products to check if there are any
    products = await get_all_products()

    if not products:
        await message.answer(
            "📚 Наш каталог в настоящее время пуст. Пожалуйста, проверьте позже!",
            reply_markup=get_main_keyboard(message.from_user.id)
        )
        return

    # Check if we have categories, if not, just show all products
    if not categories:
        await message.answer(
            "📚 У нас есть несколько товаров в наличии:",
            reply_markup=get_paginated_products_keyboard(products, 0, PRODUCTS_PER_PAGE)
        )
        return

    # If we have both products and categories, show the categories
    await message.answer(
        "📚 Выберите категорию:",
        reply_markup=get_categories_keyboard(categories)
    )


async def show_category(callback: CallbackQuery):
    """Show products in a category"""
    # Extract category ID from callback data (category:123)
    category_id = int(callback.data.split(':')[1])

    # Get products in category
    products = await get_products_by_category(category_id)

    if not products:
        await callback.message.answer(
            "В этой категории нет товаров.",
            reply_markup=get_main_keyboard(callback.from_user.id)
        )
        await callback.answer()
        return

    # Show products keyboard with pagination
    await callback.message.answer(
        "🛍 Доступные товары:",
        reply_markup=get_paginated_products_keyboard(products, 0, PRODUCTS_PER_PAGE)
    )
    await callback.answer()


async def show_all_products(callback: CallbackQuery):
    """Show all available products"""
    # Get all products
    products = await get_all_products()

    if not products:
        await callback.message.answer(
            "В настоящее время нет доступных товаров.",
            reply_markup=get_main_keyboard(callback.from_user.id)
        )
        await callback.answer()
        return

    # Show products keyboard with pagination
    await callback.message.answer(
        "🛍 Все доступные товары:",
        reply_markup=get_paginated_products_keyboard(products, 0, PRODUCTS_PER_PAGE)
    )
    await callback.answer()


async def paginate_products(callback: CallbackQuery):
    """Handle pagination of products"""
    # Parse the callback data (pagination:category_id:page)
    # If category_id is 0, it means "all products"
    parts = callback.data.split(':')
    category_id = int(parts[1])
    page = int(parts[2])

    # Get products based on category_id
    if category_id == 0:
        products = await get_all_products()
        title = "🛍 Все доступные товары:"
    else:
        products = await get_products_by_category(category_id)
        title = "🛍 Товары в категории:"

    if not products:
        await callback.message.answer(
            "Нет доступных товаров.",
            reply_markup=get_main_keyboard(callback.from_user.id)
        )
        await callback.answer()
        return

    # Show products with updated pagination
    await callback.message.edit_text(
        title,
        reply_markup=get_paginated_products_keyboard(products, page, PRODUCTS_PER_PAGE)
    )
    await callback.answer()


async def show_product_details(callback: CallbackQuery):
    """Show details for a product"""
    # Extract product ID from callback data (product:123)
    product_id = int(callback.data.split(':')[1])

    # Get product details
    product = await get_product(product_id)

    if not product:
        await callback.answer("Товар не найден.", show_alert=True)
        return

    # Format product details
    product_text = (
        f"📦 {hbold(product.title)}\n\n"
        f"{product.short_description}\n\n"
        f"Цена: {hcode(f'{product.price:.2f}')} монет"
    )

    # If product has a preview image, show it with the details
    if product.preview_image_id:
        try:
            # Try to send as photo first
            await callback.message.answer_photo(
                photo=product.preview_image_id,
                caption=product_text,
                reply_markup=get_product_details_keyboard(product.id)
            )
        except Exception:
            # If that fails, try sending as document (for GIFs)
            try:
                await callback.message.answer_document(
                    document=product.preview_image_id,
                    caption=product_text,
                    reply_markup=get_product_details_keyboard(product.id)
                )
            except Exception:
                # If both fail, just send text
                await callback.message.answer(
                    product_text,
                    reply_markup=get_product_details_keyboard(product.id)
                )
    else:
        # No preview image, just send text
        await callback.message.answer(
            product_text,
            reply_markup=get_product_details_keyboard(product.id)
        )

    await callback.answer()


async def back_to_products(callback: CallbackQuery):
    """Handle back to products button"""
    # Go back to all products
    await show_all_products(callback)


def register_catalog_handlers(dp: Dispatcher):
    """Register catalog handlers"""
    dp.message.register(cmd_catalog, Command("catalog"))
    dp.message.register(cmd_catalog, F.text == "📚 Каталог")
    dp.callback_query.register(show_category, F.data.startswith("category:"))
    dp.callback_query.register(show_all_products, F.data == "all_products")
    dp.callback_query.register(paginate_products, F.data.startswith("pagination:"))
    dp.callback_query.register(show_product_details, F.data.startswith("product:"))
    dp.callback_query.register(back_to_products, F.data == "back_to_products")