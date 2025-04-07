from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Get main menu keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📚 Catalog"),
                KeyboardButton(text="🛒 Cart")
            ],
            [
                KeyboardButton(text="💰 Balance"),
                KeyboardButton(text="👤 Profile")
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="Choose an option"
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
                InlineKeyboardButton(text="Back", callback_data="back")
            ]
        ]
    )
    return keyboard