from aiogram import Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold, hcode
from aiogram.fsm.context import FSMContext

from config import load_config
from database.methods import (
    get_all_products, 
    get_product, 
    add_product,
    update_product,
    delete_product,
    get_all_categories,
    get_user_by_username,
    update_user_balance
)
from keyboards.keyboards import (
    get_admin_keyboard,
    get_admin_products_keyboard,
    get_admin_product_actions_keyboard,
    get_admin_categories_keyboard,
    get_back_keyboard,
    get_main_keyboard,
    get_admin_confirm_delete_keyboard
)
from states.states import ProductState, AddBalanceState

# Load config to get admin IDs
config = load_config()
ADMIN_IDS = config.admin_ids

async def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS

async def cmd_admin(message: Message):
    """Handle /admin command"""
    # Check if user is admin
    if not await is_admin(message.from_user.id):
        await message.answer("You don't have access to admin panel.")
        return
    
    await message.answer(
        f"👑 {hbold('Admin Panel')}\n\n"
        f"Welcome to the admin panel. Select an action:",
        reply_markup=get_admin_keyboard()
    )

async def admin_manage_products(callback: CallbackQuery):
    """Show products management menu"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return
    
    products = await get_all_products(available_only=False)
    
    if not products:
        await callback.message.answer(
            "No products in database. Add your first product!",
            reply_markup=get_admin_keyboard()
        )
        await callback.answer()
        return
    
    await callback.message.answer(
        "🏪 Products Management\n\n"
        "Select a product to manage:",
        reply_markup=get_admin_products_keyboard(products)
    )
    await callback.answer()

async def admin_product_actions(callback: CallbackQuery):
    """Show actions for a specific product"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return
    
    # Extract product ID from callback data (admin_product:123)
    product_id = int(callback.data.split(':')[1])
    
    # Get product details
    product = await get_product(product_id)
    
    if not product:
        await callback.answer("Product not found.", show_alert=True)
        return
    
    # Get category name safely
    category_name = "None"
    try:
        if product.category:
            category_name = product.category.name
    except Exception:
        # If there's an error accessing the category, just use None
        category_name = "None"
    
    # Format product details
    product_text = (
        f"📦 {hbold(product.title)}\n\n"
        f"Description: {product.short_description}\n"
        f"Price: {hcode(f'{product.price:.2f}')} coins\n"
        f"Available: {'✅' if product.available else '❌'}\n"
        f"Category: {category_name}\n"
        f"File ID: {product.file_id or 'Not set'}\n"
        f"Preview Image: {'Set' if product.preview_image_id else 'Not set'}\n\n"
        f"What do you want to do with this product?"
    )
    
    # If product has a preview image, show it with the details
    if product.preview_image_id:
        try:
            # Try to send as photo first
            await callback.message.answer_photo(
                photo=product.preview_image_id,
                caption=product_text,
                reply_markup=get_admin_product_actions_keyboard(product_id)
            )
        except Exception:
            # If that fails, try sending as document (for GIFs)
            try:
                await callback.message.answer_document(
                    document=product.preview_image_id,
                    caption=product_text,
                    reply_markup=get_admin_product_actions_keyboard(product_id)
                )
            except Exception:
                # If both fail, just send text
                await callback.message.answer(
                    product_text,
                    reply_markup=get_admin_product_actions_keyboard(product_id)
                )
    else:
        # No preview image, just send text
        await callback.message.answer(
            product_text,
            reply_markup=get_admin_product_actions_keyboard(product_id)
        )
    
    await callback.answer()

async def admin_add_product(callback: CallbackQuery, state: FSMContext):
    """Start process of adding a new product"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return
    
    # Set state for product addition
    await state.set_state(ProductState.title)
    
    await callback.message.answer(
        "🆕 Adding New Product\n\n"
        "Please enter the product title:",
        reply_markup=get_back_keyboard()
    )
    await callback.answer()

async def admin_add_product_title(message: Message, state: FSMContext):
    """Process product title input"""
    if not await is_admin(message.from_user.id):
        await message.answer("Access denied")
        await state.clear()
        return
    
    # Save title to state
    await state.update_data(title=message.text)
    
    # Move to next state
    await state.set_state(ProductState.description)
    
    await message.answer(
        "Great! Now enter a short description for the product:"
    )

async def admin_add_product_description(message: Message, state: FSMContext):
    """Process product description input"""
    if not await is_admin(message.from_user.id):
        await message.answer("Access denied")
        await state.clear()
        return
    
    # Save description to state
    await state.update_data(short_description=message.text)
    
    # Move to next state
    await state.set_state(ProductState.price)
    
    await message.answer(
        "Now enter the price in coins (numbers only, can include decimal point):"
    )

async def admin_add_product_price(message: Message, state: FSMContext):
    """Process product price input"""
    if not await is_admin(message.from_user.id):
        await message.answer("Access denied")
        await state.clear()
        return
    
    # Validate price
    try:
        price = float(message.text)
        if price <= 0:
            raise ValueError("Price must be positive")
    except ValueError:
        await message.answer("Please enter a valid positive number for price.")
        return
    
    # Save price to state
    await state.update_data(price=price)
    
    # Get categories for selection
    categories = await get_all_categories()
    
    # Move to next state
    await state.set_state(ProductState.category)
    
    if categories:
        await message.answer(
            "Select a category for the product:",
            reply_markup=get_admin_categories_keyboard(categories)
        )
    else:
        # No categories, proceed directly to preview image
        await state.set_state(ProductState.preview_image)
        await message.answer(
            "No categories found. You can create categories later.\n\n"
            "Now send me a preview image for this product (.JPG, .PNG, or .GIF) or type 'skip' to skip this step:"
        )

async def admin_add_product_category(callback: CallbackQuery, state: FSMContext):
    """Process product category selection"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        await state.clear()
        return
    
    # Extract category ID from callback data (admin_category:123)
    category_id = int(callback.data.split(':')[1])
    
    # Save category to state
    await state.update_data(category_id=category_id)
    
    # Move to preview image state
    await state.set_state(ProductState.preview_image)
    
    await callback.message.answer(
        "Now send me a preview image for this product (.JPG, .PNG, or .GIF) or type 'skip' to skip this step:"
    )
    await callback.answer()

async def admin_add_product_preview_image(message: Message, state: FSMContext):
    """Process product preview image upload"""
    if not await is_admin(message.from_user.id):
        await message.answer("Access denied")
        await state.clear()
        return
    
    preview_image_id = None
    
    # Check if message contains a photo or document
    if message.photo:
        # Get the largest photo (last in the array)
        preview_image_id = message.photo[-1].file_id
    elif message.document and message.document.mime_type in ['image/jpeg', 'image/png', 'image/gif']:
        preview_image_id = message.document.file_id
    elif message.text and message.text.lower() == 'skip':
        preview_image_id = None
    else:
        await message.answer(
            "Please send a photo in JPG, PNG, or GIF format, or type 'skip' to skip this step."
        )
        return
    
    # Save preview_image_id to state
    await state.update_data(preview_image_id=preview_image_id)
    
    # Move to next state
    await state.set_state(ProductState.file)
    
    await message.answer(
        "Now send me the file for this product or type 'skip' to skip this step:"
    )

async def admin_add_product_file(message: Message, state: FSMContext):
    """Process product file upload"""
    if not await is_admin(message.from_user.id):
        await message.answer("Access denied")
        await state.clear()
        return
    
    file_id = None
    
    # Check if message contains a document
    if message.document:
        file_id = message.document.file_id
    elif message.text and message.text.lower() == 'skip':
        file_id = None
    else:
        await message.answer(
            "Please send a file or type 'skip' to skip this step."
        )
        return
    
    # Save file_id to state
    await state.update_data(file_id=file_id)
    
    # Move to next state
    await state.set_state(ProductState.available)
    
    await message.answer(
        "Is this product available for purchase? Reply with 'yes' or 'no':"
    )

async def admin_add_product_available(message: Message, state: FSMContext):
    """Process product availability input"""
    if not await is_admin(message.from_user.id):
        await message.answer("Access denied")
        await state.clear()
        return
    
    # Parse response
    available = message.text.lower() in ['yes', 'y', 'true', 'да']
    
    # Save availability to state
    await state.update_data(available=available)
    
    # Get all data from state
    data = await state.get_data()
    
    # Create product
    product = await add_product(data)
    
    if product:
        await message.answer(
            f"✅ Product '{product.title}' has been successfully added!",
            reply_markup=get_admin_keyboard()
        )
    else:
        await message.answer(
            "❌ Failed to add product. Please try again.",
            reply_markup=get_admin_keyboard()
        )
    
    # Clear state
    await state.clear()

async def admin_edit_product(callback: CallbackQuery, state: FSMContext):
    """Start process of editing a product"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return
    
    # Extract product ID from callback data (admin_edit_product:123)
    product_id = int(callback.data.split(':')[1])
    
    # Get product details
    product = await get_product(product_id)
    
    if not product:
        await callback.answer("Product not found.", show_alert=True)
        return
    
    # Save product_id to state
    await state.update_data(product_id=product_id)
    
    # Set initial state for product editing
    await state.set_state(ProductState.title)
    
    await callback.message.answer(
        f"🔄 Editing product: {hbold(product.title)}\n\n"
        f"Enter new title or type 'skip' to keep current:"
    )
    await callback.answer()

async def admin_edit_product_title(message: Message, state: FSMContext):
    """Process editing product title"""
    if not await is_admin(message.from_user.id):
        await message.answer("Access denied")
        await state.clear()
        return
    
    data = await state.get_data()
    product_id = data.get('product_id')
    
    # Get current product
    product = await get_product(product_id)
    
    if message.text.lower() != 'skip':
        await state.update_data(title=message.text)
    else:
        await state.update_data(title=product.title)
    
    # Move to next state
    await state.set_state(ProductState.description)
    
    await message.answer(
        f"Current description: {product.short_description}\n\n"
        f"Enter new description or type 'skip' to keep current:"
    )

async def admin_edit_product_description(message: Message, state: FSMContext):
    """Process editing product description"""
    if not await is_admin(message.from_user.id):
        await message.answer("Access denied")
        await state.clear()
        return
    
    data = await state.get_data()
    product_id = data.get('product_id')
    
    # Get current product
    product = await get_product(product_id)
    
    if message.text.lower() != 'skip':
        await state.update_data(short_description=message.text)
    else:
        await state.update_data(short_description=product.short_description)
    
    # Move to next state
    await state.set_state(ProductState.price)
    
    await message.answer(
        f"Current price: {product.price} coins\n\n"
        f"Enter new price or type 'skip' to keep current:"
    )

async def admin_edit_product_price(message: Message, state: FSMContext):
    """Process editing product price"""
    if not await is_admin(message.from_user.id):
        await message.answer("Access denied")
        await state.clear()
        return
    
    data = await state.get_data()
    product_id = data.get('product_id')
    
    # Get current product
    product = await get_product(product_id)
    
    if message.text.lower() != 'skip':
        try:
            price = float(message.text)
            if price <= 0:
                raise ValueError("Price must be positive")
            await state.update_data(price=price)
        except ValueError:
            await message.answer("Please enter a valid positive number for price or 'skip'.")
            return
    else:
        await state.update_data(price=product.price)
    
    # Get categories for selection
    categories = await get_all_categories()
    
    # Move to next state
    await state.set_state(ProductState.category)
    
    if categories:
        current_category = f"Current category: {product.category.name if product.category else 'None'}\n\n"
        await message.answer(
            f"{current_category}Select a new category or click 'Skip' to keep current:",
            reply_markup=get_admin_categories_keyboard(categories, include_skip=True)
        )
    else:
        await message.answer(
            "No categories found. Keeping current category.\n\n"
            "Send me a new preview image for this product (.JPG, .PNG, or .GIF) or type 'skip' to keep current:"
        )
        await state.update_data(category_id=product.category_id)
        await state.set_state(ProductState.preview_image)

async def admin_edit_product_category(callback: CallbackQuery, state: FSMContext):
    """Process editing product category"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        await state.clear()
        return
    
    data = await state.get_data()
    product_id = data.get('product_id')
    
    # Get current product
    product = await get_product(product_id)
    
    # Check if skip was selected
    if callback.data == 'admin_category:skip':
        await state.update_data(category_id=product.category_id)
    else:
        # Extract category ID from callback data (admin_category:123)
        category_id = int(callback.data.split(':')[1])
        await state.update_data(category_id=category_id)
    
    # Move to preview image state
    await state.set_state(ProductState.preview_image)
    
    # If product has a preview image, show it
    preview_message = "Send me a new preview image for this product (.JPG, .PNG, or .GIF) or type 'skip' to keep current:"
    
    if product.preview_image_id:
        try:
            await callback.message.answer_photo(
                photo=product.preview_image_id,
                caption="Current preview image.\n" + preview_message
            )
        except Exception:
            # If showing photo fails, try as document (might be a GIF)
            try:
                await callback.message.answer_document(
                    document=product.preview_image_id,
                    caption="Current preview image.\n" + preview_message
                )
            except Exception:
                await callback.message.answer(
                    f"Current preview image ID: {product.preview_image_id}\n\n" + preview_message
                )
    else:
        await callback.message.answer(
            "No current preview image.\n" + preview_message
        )
    
    await callback.answer()

async def admin_edit_product_preview_image(message: Message, state: FSMContext):
    """Process editing product preview image"""
    if not await is_admin(message.from_user.id):
        await message.answer("Access denied")
        await state.clear()
        return
    
    data = await state.get_data()
    product_id = data.get('product_id')
    
    # Get current product
    product = await get_product(product_id)
    
    if message.photo:
        # Get the largest photo (last in the array)
        preview_image_id = message.photo[-1].file_id
        await state.update_data(preview_image_id=preview_image_id)
    elif message.document and message.document.mime_type in ['image/jpeg', 'image/png', 'image/gif']:
        preview_image_id = message.document.file_id
        await state.update_data(preview_image_id=preview_image_id)
    elif message.text and message.text.lower() == 'skip':
        await state.update_data(preview_image_id=product.preview_image_id)
    else:
        await message.answer(
            "Please send a photo in JPG, PNG, or GIF format, or type 'skip' to keep current."
        )
        return
    
    # Move to next state
    await state.set_state(ProductState.file)
    
    await message.answer(
        f"Current file ID: {product.file_id or 'Not set'}\n\n"
        f"Send me the new file for this product or type 'skip' to keep current:"
    )

async def admin_edit_product_file(message: Message, state: FSMContext):
    """Process editing product file"""
    if not await is_admin(message.from_user.id):
        await message.answer("Access denied")
        await state.clear()
        return
    
    data = await state.get_data()
    product_id = data.get('product_id')
    
    # Get current product
    product = await get_product(product_id)
    
    if message.document:
        file_id = message.document.file_id
        await state.update_data(file_id=file_id)
    elif message.text and message.text.lower() == 'skip':
        await state.update_data(file_id=product.file_id)
    else:
        await message.answer(
            "Please send a file or type 'skip' to keep current."
        )
        return
    
    # Move to next state
    await state.set_state(ProductState.available)
    
    await message.answer(
        f"Currently available: {'Yes' if product.available else 'No'}\n\n"
        f"Is this product available for purchase? Reply with 'yes' or 'no':"
    )

async def admin_edit_product_available(message: Message, state: FSMContext):
    """Process editing product availability"""
    if not await is_admin(message.from_user.id):
        await message.answer("Access denied")
        await state.clear()
        return
    
    # Parse response
    available = message.text.lower() in ['yes', 'y', 'true', 'да']
    
    # Save availability to state
    await state.update_data(available=available)
    
    # Get all data from state
    data = await state.get_data()
    
    # Update product
    success = await update_product(data['product_id'], data)
    
    if success:
        await message.answer(
            "✅ Product has been successfully updated!",
            reply_markup=get_admin_keyboard()
        )
    else:
        await message.answer(
            "❌ Failed to update product. Please try again.",
            reply_markup=get_admin_keyboard()
        )
    
    # Clear state
    await state.clear()

async def admin_delete_product(callback: CallbackQuery, state: FSMContext):
    """Start process of deleting a product"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return
    
    # Extract product ID from callback data (admin_delete_product:123)
    product_id = int(callback.data.split(':')[1])
    
    # Get product details
    product = await get_product(product_id)
    
    if not product:
        await callback.answer("Product not found.", show_alert=True)
        return
    
    # Save product_id to state for confirmation
    await state.update_data(product_id=product_id)
    
    await callback.message.answer(
        f"⚠️ {hbold('Confirm Delete')}\n\n"
        f"You are about to delete the product: {hbold(product.title)}\n\n"
        f"This action cannot be undone. Are you sure?",
        reply_markup=get_admin_confirm_delete_keyboard(product_id)
    )
    await callback.answer()

async def admin_confirm_delete_product(callback: CallbackQuery, state: FSMContext):
    """Confirm product deletion"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return
    
    # Extract product ID from callback data (admin_confirm_delete:123)
    product_id = int(callback.data.split(':')[1])
    
    # Delete product
    success = await delete_product(product_id)
    
    if success:
        await callback.message.answer(
            "✅ Product has been successfully deleted!",
            reply_markup=get_admin_keyboard()
        )
    else:
        await callback.message.answer(
            "❌ Failed to delete product. Please try again.",
            reply_markup=get_admin_keyboard()
        )
    
    # Clear state
    await state.clear()
    await callback.answer()

async def admin_add_balance(callback: CallbackQuery, state: FSMContext):
    """Start process of adding balance to a user"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return
    
    # Set state for balance addition
    await state.set_state(AddBalanceState.username)
    
    await callback.message.answer(
        "💰 Add Balance to User\n\n"
        "Please enter the username (without @) of the user you want to add balance to:",
        reply_markup=get_back_keyboard()
    )
    await callback.answer()

async def admin_add_balance_username(message: Message, state: FSMContext):
    """Process username input for adding balance"""
    if not await is_admin(message.from_user.id):
        await message.answer("Access denied")
        await state.clear()
        return
    
    username = message.text.strip().replace('@', '')
    
    # Find user by username
    user = await get_user_by_username(username)
    
    if not user:
        await message.answer(
            "User not found. Please check the username and try again.",
            reply_markup=get_admin_keyboard()
        )
        await state.clear()
        return
    
    # Save user details to state
    await state.update_data(user_id=user.telegram_id, username=username, current_balance=user.balance)
    
    # Move to next state
    await state.set_state(AddBalanceState.amount)
    
    await message.answer(
        f"User found: @{username}\n"
        f"Current balance: {hbold(f'{user.balance:.2f}')} coins\n\n"
        f"Enter the amount to add (can be negative to subtract):"
    )

async def admin_add_balance_amount(message: Message, state: FSMContext):
    """Process amount input for adding balance"""
    if not await is_admin(message.from_user.id):
        await message.answer("Access denied")
        await state.clear()
        return
    
    # Validate amount
    try:
        amount = float(message.text)
    except ValueError:
        await message.answer("Please enter a valid number.")
        return
    
    # Get user data from state
    data = await state.get_data()
    user_id = data.get('user_id')
    username = data.get('username')
    current_balance = data.get('current_balance', 0)
    
    # Calculate new balance
    new_balance = current_balance + amount
    
    # Update user's balance
    success = await update_user_balance(user_id, new_balance)
    
    if success:
        await message.answer(
            f"✅ Balance updated successfully!\n\n"
            f"User: @{username}\n"
            f"Previous balance: {hcode(f'{current_balance:.2f}')} coins\n"
            f"Amount added: {hcode(f'{amount:.2f}')} coins\n"
            f"New balance: {hbold(f'{new_balance:.2f}')} coins",
            reply_markup=get_admin_keyboard()
        )
    else:
        await message.answer(
            "❌ Failed to update balance. Please try again.",
            reply_markup=get_admin_keyboard()
        )
    
    # Clear state
    await state.clear()

async def admin_back(callback: CallbackQuery, state: FSMContext):
    """Handle back button in admin panel"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return
    
    # Clear state if any
    current_state = await state.get_state()
    if current_state:
        await state.clear()
    
    await callback.message.answer(
        "👑 Admin Panel",
        reply_markup=get_admin_keyboard()
    )
    await callback.answer()

async def debug_db_status(message: Message):
    """Debug handler to check DB status - only available to admins"""
    if not await is_admin(message.from_user.id):
        return
    
    # Get product and category counts
    products = await get_all_products(available_only=False)
    categories = await get_all_categories()
    
    debug_text = (
        f"🔍 {hbold('Database Status')}\n\n"
        f"Products count: {len(products)}\n"
        f"Categories count: {len(categories)}\n\n"
    )
    
    # Show some product details for debugging
    if products:
        debug_text += f"{hbold('First 5 products:')}\n"
        for i, product in enumerate(products[:5], 1):
            debug_text += (
                f"{i}. ID: {product.id}, Title: {product.title}, "
                f"Price: {product.price}, Available: {product.available}\n"
            )
    
    await message.answer(debug_text)

def register_admin_handlers(dp: Dispatcher):
    """Register admin handlers"""
    # Command handlers
    dp.message.register(cmd_admin, Command("admin"))
    dp.message.register(debug_db_status, Command("debug_db"))
    
    # Admin panel navigation
    dp.callback_query.register(admin_manage_products, F.data == "admin_manage_products")
    dp.callback_query.register(admin_product_actions, F.data.startswith("admin_product:"))
    dp.callback_query.register(admin_back, F.data == "admin_back")
    
    # Add product handlers
    dp.callback_query.register(admin_add_product, F.data == "admin_add_product")
    dp.message.register(admin_add_product_title, ProductState.title)
    dp.message.register(admin_add_product_description, ProductState.description)
    dp.message.register(admin_add_product_price, ProductState.price)
    dp.callback_query.register(admin_add_product_category, F.data.startswith("admin_category:"))
    dp.message.register(admin_add_product_preview_image, ProductState.preview_image)
    dp.message.register(admin_add_product_file, ProductState.file)
    dp.message.register(admin_add_product_available, ProductState.available)
    
    # Edit product handlers
    dp.callback_query.register(admin_edit_product, F.data.startswith("admin_edit_product:"))
    dp.message.register(admin_edit_product_title, ProductState.title)
    dp.message.register(admin_edit_product_description, ProductState.description)
    dp.message.register(admin_edit_product_price, ProductState.price)
    dp.callback_query.register(admin_edit_product_category, F.data.startswith("admin_category:"))
    dp.message.register(admin_edit_product_preview_image, ProductState.preview_image)
    dp.message.register(admin_edit_product_file, ProductState.file)
    dp.message.register(admin_edit_product_available, ProductState.available)
    
    # Delete product handlers
    dp.callback_query.register(admin_delete_product, F.data.startswith("admin_delete_product:"))
    dp.callback_query.register(admin_confirm_delete_product, F.data.startswith("admin_confirm_delete:"))
    
    # Add balance handlers
    dp.callback_query.register(admin_add_balance, F.data == "admin_add_balance")
    dp.message.register(admin_add_balance_username, AddBalanceState.username)
    dp.message.register(admin_add_balance_amount, AddBalanceState.amount)