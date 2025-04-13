from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import math
from config import load_config

# Load config to get admin IDs
config = load_config()
ADMIN_IDS = config.admin_ids


def get_main_keyboard(user_id=None) -> ReplyKeyboardMarkup:
    """Get main menu keyboard, with admin button if user is admin"""
    buttons = [
        [
            KeyboardButton(text="📚 Каталог"),
            KeyboardButton(text="💰 Баланс"),
        ],
        [
            KeyboardButton(text="👤 Профиль"),
            KeyboardButton(text="📞 Поддержка")
        ]
    ]

    # Add admin button if user is admin
    if user_id in ADMIN_IDS:
        buttons.append([KeyboardButton(text="👑 Панель администратора")])

    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Выберите опцию"
    )
    return keyboard


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Get admin panel keyboard (Updated with Newsletter button)"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏪 Управление товарами", callback_data="admin_manage_products")
            ],
            [
                InlineKeyboardButton(text="🆕 Добавить товар", callback_data="admin_add_product")
            ],
            [
                InlineKeyboardButton(text="💰 Добавить баланс пользователю", callback_data="admin_add_balance")
            ],
            [
                InlineKeyboardButton(text="📊 Статистика", callback_data="admin_statistics")
            ],
            [
                InlineKeyboardButton(text="📨 Рассылка", callback_data="admin_newsletter")
            ],
            [
                InlineKeyboardButton(text="↩️ Назад в главное меню", callback_data="back_to_menu")
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
                text=f"{status} {product.title} - {product.price:.2f} монет",
                callback_data=f"admin_product:{product.id}"
            )
        ])

    # Add navigation buttons
    buttons.append([
        InlineKeyboardButton(text="➕ Добавить новый товар", callback_data="admin_add_product")
    ])
    buttons.append([
        InlineKeyboardButton(text="↩️ Назад в панель администратора", callback_data="admin_back")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_product_actions_keyboard(product_id) -> InlineKeyboardMarkup:
    """Get keyboard with actions for a specific product"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Редактировать",
                    callback_data=f"admin_edit_product:{product_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Удалить",
                    callback_data=f"admin_delete_product:{product_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="↩️ Назад к товарам",
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
                text="Пропустить (оставить текущую)",
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
                    text="✅ Да, удалить",
                    callback_data=f"admin_confirm_delete:{product_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Нет, отмена",
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
                InlineKeyboardButton(text="🛍 Мои покупки", callback_data="my_purchases")
            ],
            [
                InlineKeyboardButton(text="💰 Баланс", callback_data="show_balance")
            ],
            [
                InlineKeyboardButton(text="📚 Перейти в каталог", callback_data="open_catalog")
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
        InlineKeyboardButton(text="Все товары", callback_data="all_products")
    ])

    # Add "Back to Menu" button
    buttons.append([
        InlineKeyboardButton(text="Назад в меню", callback_data="back_to_menu")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_products_keyboard(products) -> InlineKeyboardMarkup:
    """Get products keyboard"""
    buttons = []

    # Add product buttons (up to 10 products per page for simplicity)
    for product in products[:10]:
        buttons.append([
            InlineKeyboardButton(
                text=f"{product.title} - {product.price:.2f} монет",
                callback_data=f"product:{product.id}"
            )
        ])

    # Add navigation buttons
    buttons.append([
        InlineKeyboardButton(text="Назад к категориям", callback_data="back_to_categories")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_paginated_products_keyboard(products, current_page, per_page) -> InlineKeyboardMarkup:
    """Get products keyboard with pagination"""
    buttons = []

    # Calculate start and end indices for the current page
    start_idx = current_page * per_page
    end_idx = min(start_idx + per_page, len(products))

    # Get total number of pages
    total_pages = math.ceil(len(products) / per_page)

    # Add product buttons for the current page
    for product in products[start_idx:end_idx]:
        buttons.append([
            InlineKeyboardButton(
                text=f"{product.title} - {product.price:.2f} монет",
                callback_data=f"product:{product.id}"
            )
        ])

    # Add pagination buttons
    pagination_buttons = []

    # Add "Previous" button if not on the first page
    if current_page > 0:
        pagination_buttons.append(
            InlineKeyboardButton(
                text="◀️ Предыдущая",
                callback_data=f"pagination:0:{current_page - 1}"
            )
        )

    # Add page indicator
    pagination_buttons.append(
        InlineKeyboardButton(
            text=f"📄 {current_page + 1}/{total_pages}",
            callback_data="none"  # This button does nothing when clicked
        )
    )

    # Add "Next" button if not on the last page
    if current_page < total_pages - 1:
        pagination_buttons.append(
            InlineKeyboardButton(
                text="Следующая ▶️",
                callback_data=f"pagination:0:{current_page + 1}"
            )
        )

    if pagination_buttons:
        buttons.append(pagination_buttons)

    # Add navigation buttons
    buttons.append([
        InlineKeyboardButton(text="Назад к категориям", callback_data="back_to_categories")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_product_details_keyboard(product_id) -> InlineKeyboardMarkup:
    """Get product details keyboard with buy button"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🛒 Купить", callback_data=f"buy_product:{product_id}")
            ],
            [
                InlineKeyboardButton(text="Назад к товарам", callback_data="back_to_products")
            ]
        ]
    )
    return keyboard


def get_purchase_confirmation_keyboard(product_id) -> InlineKeyboardMarkup:
    """Get purchase confirmation keyboard"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_purchase:{product_id}")
            ],
            [
                InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_purchase")
            ]
        ]
    )
    return keyboard


def get_back_keyboard() -> InlineKeyboardMarkup:
    """Simple back keyboard"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="↩️ Назад", callback_data="admin_back")
            ]
        ]
    )
    return keyboard


def get_balance_topup_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard with balance top-up options"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="500 монет (~$5)",
                    callback_data="topup:500"
                )
            ],
            [
                InlineKeyboardButton(
                    text="1000 монет (~$10)",
                    callback_data="topup:1000"
                )
            ],
            [
                InlineKeyboardButton(
                    text="3000 монет (~$30)",
                    callback_data="topup:3000"
                )
            ],
            [
                InlineKeyboardButton(
                    text="10000 монет (~$100)",
                    callback_data="topup:10000"
                )
            ],
            [
                InlineKeyboardButton(
                    text="↩️ Назад",
                    callback_data="show_balance"
                )
            ]
        ]
    )
    return keyboard


def get_payment_methods_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard with payment methods - only CryptoCloud now"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💎 CryptoCloud",
                    callback_data="payment_method:cryptocloud"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data="cancel_payment"
                )
            ]
        ]
    )
    return keyboard


def get_payment_link_keyboard(payment_link: str) -> InlineKeyboardMarkup:
    """Get keyboard with payment link button"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💳 Оплатить сейчас",
                    url=payment_link
                )
            ],
            [
                InlineKeyboardButton(
                    text="↩️ Назад в главное меню",
                    callback_data="back_to_menu"
                )
            ]
        ]
    )
    return keyboard


def get_payment_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Get payment confirmation keyboard"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💳 Оплатить сейчас",
                    callback_data="confirm_payment"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data="cancel_payment"
                )
            ]
        ]
    )
    return keyboard


def get_balance_keyboard() -> InlineKeyboardMarkup:
    """Get balance page keyboard with top-up option"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💳 Пополнить баланс",
                    callback_data="topup_balance"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📚 Перейти в каталог",
                    callback_data="open_catalog"
                )
            ],
            [
                InlineKeyboardButton(
                    text="↩️ Назад в главное меню",
                    callback_data="back_to_menu"
                )
            ]
        ]
    )
    return keyboard


def get_support_keyboard(admin_contact: str) -> InlineKeyboardMarkup:
    """Get support menu keyboard with contact button"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📩 Связаться с поддержкой",
                    url=f"https://t.me/{admin_contact.lstrip('@')}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="↩️ Назад в главное меню",
                    callback_data="back_to_menu"
                )
            ]
        ]
    )
    return keyboard


def get_backup_keyboard() -> InlineKeyboardMarkup:
    """Get backup database keyboard"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📥 Скачать резервную копию", callback_data="admin_download_backup")
            ],
            [
                InlineKeyboardButton(text="↩️ Назад в панель администратора", callback_data="admin_back")
            ]
        ]
    )
    return keyboard


def get_newsletter_main_keyboard() -> InlineKeyboardMarkup:
    """Get newsletter main menu keyboard"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 Создать рассылку", callback_data="create_newsletter")
            ],
            [
                InlineKeyboardButton(text="📋 Мои рассылки", callback_data="my_newsletters")
            ],
            [
                InlineKeyboardButton(text="↩️ Назад в панель администратора", callback_data="admin_back")
            ]
        ]
    )
    return keyboard


def get_newsletter_list_keyboard(newsletters, page=0, per_page=5) -> InlineKeyboardMarkup:
    """Get keyboard with list of newsletters and pagination"""
    buttons = []

    # Calculate start and end indices for the current page
    start_idx = page * per_page
    end_idx = min(start_idx + per_page, len(newsletters))

    # Get total number of pages
    total_pages = math.ceil(len(newsletters) / per_page) if newsletters else 1

    # Add newsletter buttons for the current page
    for newsletter in newsletters[start_idx:end_idx]:
        # Show status emoji
        status_emoji = "✅" if newsletter.status == "sent" else "📝"

        buttons.append([
            InlineKeyboardButton(
                text=f"{status_emoji} {newsletter.title}",
                callback_data=f"view_newsletter:{newsletter.id}"
            )
        ])

    # Add pagination buttons
    pagination_buttons = []

    # Add "Previous" button if not on the first page
    if page > 0:
        pagination_buttons.append(
            InlineKeyboardButton(
                text="◀️ Предыдущая",
                callback_data=f"newsletter_page:{page - 1}"
            )
        )

    # Add page indicator
    pagination_buttons.append(
        InlineKeyboardButton(
            text=f"📄 {page + 1}/{total_pages}",
            callback_data="none"
        )
    )

    # Add "Next" button if not on the last page
    if newsletters and page < total_pages - 1:
        pagination_buttons.append(
            InlineKeyboardButton(
                text="Следующая ▶️",
                callback_data=f"newsletter_page:{page + 1}"
            )
        )

    if pagination_buttons:
        buttons.append(pagination_buttons)

    # Add back button
    buttons.append([
        InlineKeyboardButton(text="↩️ Назад", callback_data="admin_newsletter")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_newsletter_detail_keyboard(newsletter_id: int, newsletter_status: str) -> InlineKeyboardMarkup:
    """Get keyboard for newsletter details"""
    buttons = []

    if newsletter_status == "draft":
        buttons.append([
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_newsletter:{newsletter_id}")
        ])
        buttons.append([
            InlineKeyboardButton(text="🚀 Отправить сейчас", callback_data=f"send_newsletter:{newsletter_id}")
        ])

    buttons.append([
        InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_newsletter:{newsletter_id}")
    ])
    buttons.append([
        InlineKeyboardButton(text="↩️ Назад к списку", callback_data="my_newsletters")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_newsletter_creation_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for newsletter creation process"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="↩️ Отмена", callback_data="cancel_newsletter")
            ]
        ]
    )
    return keyboard


def get_newsletter_photo_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for the photo step of newsletter creation"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⏩ Пропустить фото", callback_data="skip_newsletter_photo")
            ],
            [
                InlineKeyboardButton(text="↩️ Отмена", callback_data="cancel_newsletter")
            ]
        ]
    )
    return keyboard


def get_newsletter_file_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for the file step of newsletter creation"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⏩ Пропустить вложение файла", callback_data="skip_newsletter_file")
            ],
            [
                InlineKeyboardButton(text="↩️ Отмена", callback_data="cancel_newsletter")
            ]
        ]
    )
    return keyboard


def get_newsletter_button_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for the button step of newsletter creation"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⏩ Пропустить кнопку", callback_data="skip_newsletter_button")
            ],
            [
                InlineKeyboardButton(text="↩️ Отмена", callback_data="cancel_newsletter")
            ]
        ]
    )
    return keyboard


def get_newsletter_preview_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for newsletter preview"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 Редактировать заголовок", callback_data="edit_newsletter_title")
            ],
            [
                InlineKeyboardButton(text="📝 Редактировать сообщение", callback_data="edit_newsletter_message")
            ],
            [
                InlineKeyboardButton(text="📝 Редактировать фото", callback_data="edit_newsletter_photo")
            ],
            [
                InlineKeyboardButton(text="📝 Редактировать файл", callback_data="edit_newsletter_file")
            ],
            [
                InlineKeyboardButton(text="📝 Редактировать кнопку", callback_data="edit_newsletter_button")
            ],
            [
                InlineKeyboardButton(text="💾 Сохранить черновик", callback_data="save_newsletter_draft")
            ],
            [
                InlineKeyboardButton(text="🚀 Отправить сейчас", callback_data="confirm_send_newsletter")
            ],
            [
                InlineKeyboardButton(text="↩️ Отмена", callback_data="cancel_newsletter")
            ]
        ]
    )
    return keyboard


def get_newsletter_confirm_delete_keyboard(newsletter_id: int) -> InlineKeyboardMarkup:
    """Get confirmation keyboard for newsletter deletion"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, удалить",
                    callback_data=f"confirm_delete_newsletter:{newsletter_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Нет, отмена",
                    callback_data=f"view_newsletter:{newsletter_id}"
                )
            ]
        ]
    )
    return keyboard


def get_newsletter_button_preview(text: str, url: str) -> InlineKeyboardMarkup:
    """Get preview of the newsletter button"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=text, url=url)
            ]
        ]
    )
    return keyboard