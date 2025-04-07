from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import load_config

# Load config to get admin IDs
config = load_config()
ADMIN_IDS = config.admin_ids

def get_main_keyboard(user_id=None) -> ReplyKeyboardMarkup:
    """Get main menu keyboard, with admin button if user is admin"""
    buttons = [
        [
            KeyboardButton(text="📚 Catalog"),
            KeyboardButton(text="🛒 Cart")
        ],
        [
            KeyboardButton(text="💰 Balance"),
            KeyboardButton(text="👤 Profile")
        ]
    ]
    
    # Add admin button if user is admin
    if user_id in ADMIN_IDS:
        buttons.append([KeyboardButton(text="👑 Admin Panel")])
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Choose an option"
    )
    return keyboard

def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Get admin panel keyboard"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏪 Manage Products", callback_data="admin_manage_products")
            ],
            [
                InlineKeyboardButton(text="🆕 Add Product", callback_data="admin_add_product")
            ],
            [
                InlineKeyboardButton(text="💰 Add Balance to User", callback_data="admin_add_balance")
            ],
            [
                InlineKeyboardButton(text="↩️ Back to Main Menu", callback_data="back_to_menu")
            ]
        ]
    )
    return keyboard

def get_admin_products_keyboard(products) -> InlineKeyboardMarkup:
    """Get admin products management keyboard"""
    buttons = []
    
    # Add product buttons
    for product in products:
        status = "✅" if product.available else "❌"
        buttons.append([
            InlineKeyboardButton(
                text=f"{status} {product.title} - {product.price:.2f} coins", 
                callback_data=f"admin_product:{product.id}"
            )
        ])
    
    # Add navigation buttons
    buttons.append([
        InlineKeyboardButton(text="➕ Add New Product", callback_data="admin_add_product")
    ])
    buttons.append([
        InlineKeyboardButton(text="↩️ Back to Admin Panel", callback_data="admin_back")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_product_actions_keyboard(product_id) -> InlineKeyboardMarkup:
    """Get keyboard with actions for a specific product"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Edit", 
                    callback_data=f"admin_edit_product:{product_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Delete", 
                    callback_data=f"admin_delete_product:{product_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="↩️ Back to Products", 
                    callback_data="admin_manage_products"
                )
            ]
        ]
    )
    return keyboard

def get_admin_categories_keyboard(categories, include_skip=False) -> InlineKeyboardMarkup:
    """Get categories keyboard for admin product management"""
    buttons = []
    
    # Add category buttons
    for category in categories:
        buttons.append([
            InlineKeyboardButton(
                text=category.name, 
                callback_data=f"admin_category:{category.id}"
            )
        ])
    
    # Add skip button if needed
    if include_skip:
        buttons.append([
            InlineKeyboardButton(
                text="Skip (Keep Current)", 
                callback_data="admin_category:skip"
            )
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_confirm_delete_keyboard(product_id) -> InlineKeyboardMarkup:
    """Get confirmation keyboard for product deletion"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Yes, Delete", 
                    callback_data=f"admin_confirm_delete:{product_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ No, Cancel", 
                    callback_data="admin_manage_products"
                )
            ]
        ]
    )
    return keyboard

def get_profile_keyboard() -> InlineKeyboardMarkup:
    """Get profile menu keyboard"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🛍 My Purchases", callback_data="my_purchases")
            ],
            [
                InlineKeyboardButton(text="💰 Balance", callback_data="show_balance")
            ],
            [
                InlineKeyboardButton(text="📚 Go to Catalog", callback_data="open_catalog")
            ]
        ]
    )
    return keyboard

def get_categories_keyboard(categories) -> InlineKeyboardMarkup:
    """Get categories keyboard"""
    buttons = []
    
    # Add category buttons
    for category in categories:
        buttons.append([
            InlineKeyboardButton(text=category.name, callback_data=f"category:{category.id}")
        ])
    
    # Add "All Products" button
    buttons.append([
        InlineKeyboardButton(text="All Products", callback_data="all_products")
    ])
    
    # Add "Back to Menu" button
    buttons.append([
        InlineKeyboardButton(text="Back to Menu", callback_data="back_to_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_products_keyboard(products) -> InlineKeyboardMarkup:
    """Get products keyboard"""
    buttons = []
    
    # Add product buttons (up to 10 products per page for simplicity)
    for product in products[:10]:
        buttons.append([
            InlineKeyboardButton(
                text=f"{product.title} - {product.price:.2f} coins", 
                callback_data=f"product:{product.id}"
            )
        ])
    
    # Add navigation buttons
    buttons.append([
        InlineKeyboardButton(text="Back to Categories", callback_data="back_to_categories")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_product_details_keyboard(product_id) -> InlineKeyboardMarkup:
    """Get product details keyboard with buy button"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🛒 Buy", callback_data=f"buy_product:{product_id}")
            ],
            [
                InlineKeyboardButton(text="Back to Products", callback_data="back_to_products")
            ]
        ]
    )
    return keyboard

def get_purchase_confirmation_keyboard(product_id) -> InlineKeyboardMarkup:
    """Get purchase confirmation keyboard"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Confirm", callback_data=f"confirm_purchase:{product_id}")
            ],
            [
                InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_purchase")
            ]
        ]
    )
    return keyboard

def get_back_keyboard() -> InlineKeyboardMarkup:
    """Simple back keyboard"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="↩️ Back", callback_data="admin_back")
            ]
        ]
    )
    return keyboard