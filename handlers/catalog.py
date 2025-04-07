from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold, hcode

from database.methods import get_all_categories, get_products_by_category, get_all_products, get_product
from keyboards.keyboards import get_categories_keyboard, get_products_keyboard, get_product_details_keyboard, get_main_keyboard

async def cmd_catalog(message: Message):
    """Handle /catalog command"""
    # Get all categories
    categories = await get_all_categories()
    
    if not categories:
        await message.answer(
            "📚 Our catalog is currently empty. Please check back later!",
            reply_markup=get_main_keyboard(message.from_user.id)
        )
        return
    
    # Show categories keyboard
    await message.answer(
        "📚 Select a category:",
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
            "No products found in this category.",
            reply_markup=get_main_keyboard(callback.from_user.id)
        )
        await callback.answer()
        return
    
    # Show products keyboard
    await callback.message.answer(
        "🛍 Available products:",
        reply_markup=get_products_keyboard(products)
    )
    await callback.answer()

async def show_all_products(callback: CallbackQuery):
    """Show all available products"""
    # Get all products
    products = await get_all_products()
    
    if not products:
        await callback.message.answer(
            "No products available currently.",
            reply_markup=get_main_keyboard(callback.from_user.id)
        )
        await callback.answer()
        return
    
    # Show products keyboard
    await callback.message.answer(
        "🛍 All available products:",
        reply_markup=get_products_keyboard(products)
    )
    await callback.answer()

async def show_product_details(callback: CallbackQuery):
    """Show details for a product"""
    # Extract product ID from callback data (product:123)
    product_id = int(callback.data.split(':')[1])
    
    # Get product details
    product = await get_product(product_id)
    
    if not product:
        await callback.answer("Product not found.", show_alert=True)
        return
    
    # Format product details
    product_text = (
        f"📦 {hbold(product.title)}\n\n"
        f"{product.short_description}\n\n"
        f"Price: {hcode(f'{product.price:.2f}')} coins"
    )
    
    # Show product details with buy button
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
    dp.message.register(cmd_catalog, F.text == "📚 Catalog")
    dp.callback_query.register(show_category, F.data.startswith("category:"))
    dp.callback_query.register(show_all_products, F.data == "all_products")
    dp.callback_query.register(show_product_details, F.data.startswith("product:"))
    dp.callback_query.register(back_to_products, F.data == "back_to_products")