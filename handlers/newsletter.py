import logging
import time
import asyncio
from datetime import datetime
from aiogram import Dispatcher, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold, hcode
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import load_config
from database.methods import (
    get_all_newsletters, 
    get_newsletter, 
    create_newsletter,
    update_newsletter,
    delete_newsletter,
    get_all_users_telegram_ids,
    mark_newsletter_as_sent
)
from keyboards.keyboards import (
    get_newsletter_main_keyboard,
    get_newsletter_list_keyboard,
    get_newsletter_detail_keyboard,
    get_newsletter_creation_keyboard,
    get_newsletter_photo_keyboard,
    get_newsletter_file_keyboard,
    get_newsletter_button_keyboard,
    get_newsletter_preview_keyboard,
    get_newsletter_confirm_delete_keyboard,
    get_newsletter_button_preview,
    get_admin_keyboard
)
from states.states import NewsletterState
from utils.admin import is_admin

# Load config to get admin IDs
config = load_config()
ADMIN_IDS = config.admin_ids

# Configure logging
logger = logging.getLogger(__name__)

# Helper function to check admin status
async def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS

async def show_newsletter_menu(callback: CallbackQuery):
    """Show newsletter main menu"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return
    
    await callback.message.answer(
        f"📨 {hbold('Newsletter Management')}\n\n"
        f"Here you can create and manage newsletters to send to all users.\n\n"
        f"Choose an option:",
        reply_markup=get_newsletter_main_keyboard()
    )
    await callback.answer()

async def show_my_newsletters(callback: CallbackQuery):
    """Show list of created newsletters"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return
    
    # Get all newsletters
    newsletters = await get_all_newsletters()
    
    if not newsletters:
        await callback.message.answer(
            "You haven't created any newsletters yet.",
            reply_markup=get_newsletter_main_keyboard()
        )
        await callback.answer()
        return
    
    await callback.message.answer(
        f"📋 {hbold('My Newsletters')}\n\n"
        f"Here are your newsletters (✅ = sent, 📝 = draft):",
        reply_markup=get_newsletter_list_keyboard(newsletters)
    )
    await callback.answer()

async def paginate_newsletters(callback: CallbackQuery):
    """Handle pagination of newsletters"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return
    
    # Parse the callback data (newsletter_page:page)
    page = int(callback.data.split(':')[1])
    
    # Get all newsletters
    newsletters = await get_all_newsletters()
    
    if not newsletters:
        await callback.message.answer(
            "You haven't created any newsletters yet.",
            reply_markup=get_newsletter_main_keyboard()
        )
        await callback.answer()
        return
    
    # Update the message with the new page
    await callback.message.edit_text(
        f"📋 {hbold('My Newsletters')}\n\n"
        f"Here are your newsletters (✅ = sent, 📝 = draft):",
        reply_markup=get_newsletter_list_keyboard(newsletters, page)
    )
    await callback.answer()

async def view_newsletter(callback: CallbackQuery):
    """View a specific newsletter"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return
    
    # Extract newsletter ID from callback data (view_newsletter:123)
    newsletter_id = int(callback.data.split(':')[1])
    
    # Get newsletter details
    newsletter = await get_newsletter(newsletter_id)
    
    if not newsletter:
        await callback.answer("Newsletter not found.", show_alert=True)
        return
    
    # Format status
    status_text = "✅ Sent" if newsletter.status == "sent" else "📝 Draft"
    
    # Format statistics
    stats_text = ""
    if newsletter.status == "sent" and newsletter.sent_at:
        stats_text = (
            f"\n\n{hbold('Sending Statistics:')}\n"
            f"• Sent at: {newsletter.sent_at.strftime('%Y-%m-%d %H:%M')}\n"
            f"• Recipients: {newsletter.recipients_count}\n"
            f"• Successful: {newsletter.success_count}\n"
            f"• Failed: {newsletter.error_count}\n"
            f"• Send time: {newsletter.send_time:.1f} seconds"
        )
    
    # Format button info
    button_text = ""
    if newsletter.button_text and newsletter.button_url:
        button_text = f"\n\n{hbold('Button:')}\nText: {newsletter.button_text}\nURL: {newsletter.button_url}"
    
    # Format newsletter details
    newsletter_text = (
        f"📨 {hbold(newsletter.title)}\n\n"
        f"Status: {status_text}\n"
        f"Created: {newsletter.created_at.strftime('%Y-%m-%d %H:%M')}\n"
        f"{stats_text}\n\n"
        f"{hbold('Message:')}\n{newsletter.message_text}"
        f"{button_text}"
    )
    
    # Create appropriate keyboard based on newsletter status
    keyboard = get_newsletter_detail_keyboard(newsletter.id, newsletter.status)
    
    # If there's a photo, send with photo
    if newsletter.photo_id:
        try:
            await callback.message.answer_photo(
                photo=newsletter.photo_id,
                caption=newsletter_text,
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Error sending newsletter photo: {e}")
            # If photo send fails, just send as text
            await callback.message.answer(
                f"Note: Unable to display photo.\n\n{newsletter_text}",
                reply_markup=keyboard
            )
    # If there's a file, mention it
    elif newsletter.file_id:
        file_info = f"\n\n{hbold('Attached File:')}\n{newsletter.file_name or 'File attachment'}"
        await callback.message.answer(
            f"{newsletter_text}{file_info}",
            reply_markup=keyboard
        )
    else:
        # No photo or file, just send text
        await callback.message.answer(
            newsletter_text,
            reply_markup=keyboard
        )
    
    await callback.answer()

async def start_create_newsletter(callback: CallbackQuery, state: FSMContext):
    """Start process of creating a new newsletter"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return
    
    # Set state for newsletter creation
    await state.set_state(NewsletterState.title)
    
    await callback.message.answer(
        f"📝 {hbold('Create Newsletter')}\n\n"
        f"Let's create a new newsletter to send to all users.\n\n"
        f"First, please enter a title for your newsletter:",
        reply_markup=get_newsletter_creation_keyboard()
    )
    await callback.answer()

async def process_newsletter_title(message: Message, state: FSMContext):
    """Process newsletter title input"""
    if not await is_admin(message.from_user.id):
        await message.answer("Access denied")
        await state.clear()
        return
    
    # Validate title length
    if len(message.text) > 200:
        await message.answer(
            "Title is too long (max 200 characters). Please enter a shorter title:"
        )
        return
    
    # Save title to state
    await state.update_data(title=message.text)
    
    # Move to next state
    await state.set_state(NewsletterState.message_text)
    
    await message.answer(
        f"Great! Now enter the message text for your newsletter:\n\n"
        f"Note: HTML formatting is supported. You can use:\n"
        f"• <b>Bold text</b>\n"
        f"• <i>Italic text</i>\n"
        f"• <u>Underlined text</u>\n"
        f"• <code>Code</code>\n"
        f"• <a href='https://example.com'>Link</a>\n\n"
        f"Enter your message text:",
        reply_markup=get_newsletter_creation_keyboard()
    )

async def process_newsletter_message(message: Message, state: FSMContext):
    """Process newsletter message text input"""
    if not await is_admin(message.from_user.id):
        await message.answer("Access denied")
        await state.clear()
        return
    
    # Save message text to state
    await state.update_data(message_text=message.text)
    
    # Move to next state
    await state.set_state(NewsletterState.photo)
    
    await message.answer(
        f"Good! Now you can add a photo to your newsletter (optional).\n\n"
        f"Send me a photo or click 'Skip Photo' to continue without a photo:",
        reply_markup=get_newsletter_photo_keyboard()
    )

async def process_newsletter_photo(message: Message, state: FSMContext):
    """Process newsletter photo upload"""
    if not await is_admin(message.from_user.id):
        await message.answer("Access denied")
        await state.clear()
        return
    
    photo_id = None
    
    # Check if message contains a photo
    if message.photo:
        # Get the largest photo (last in the array)
        photo_id = message.photo[-1].file_id
    elif message.document and message.document.mime_type and message.document.mime_type.startswith('image/'):
        # Handle image sent as document (GIF, etc.)
        photo_id = message.document.file_id
    else:
        await message.answer(
            "Please send a photo in JPG, PNG, GIF, or WEBP format, or click 'Skip Photo'."
        )
        return
    
    # Save photo_id to state
    await state.update_data(photo_id=photo_id)
    
    # Move to next state
    await state.set_state(NewsletterState.file)
    
    await message.answer(
        f"Photo added! Now you can attach a file to your newsletter (optional).\n\n"
        f"Send me a file (max 50 MB) or click 'Skip File Attachment' to continue without a file:",
        reply_markup=get_newsletter_file_keyboard()
    )

async def skip_newsletter_photo(callback: CallbackQuery, state: FSMContext):
    """Skip adding a photo to the newsletter"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return
    
    # Save null photo_id to state
    await state.update_data(photo_id=None)
    
    # Move to next state
    await state.set_state(NewsletterState.file)
    
    await callback.message.answer(
        f"Photo skipped. Now you can attach a file to your newsletter (optional).\n\n"
        f"Send me a file (max 50 MB) or click 'Skip File Attachment' to continue without a file:",
        reply_markup=get_newsletter_file_keyboard()
    )
    await callback.answer()

async def process_newsletter_file(message: Message, state: FSMContext):
    """Process newsletter file upload"""
    if not await is_admin(message.from_user.id):
        await message.answer("Access denied")
        await state.clear()
        return
    
    # Check if message contains a document
    if not message.document:
        await message.answer(
            "Please send a file or click 'Skip File Attachment'."
        )
        return
    
    # Check file size (50 MB limit = 50 * 1024 * 1024 bytes)
    if message.document.file_size > 50 * 1024 * 1024:
        await message.answer(
            "File is too large (max 50 MB). Please send a smaller file:"
        )
        return
    
    # Save file info to state
    await state.update_data(
        file_id=message.document.file_id,
        file_name=message.document.file_name
    )
    
    # Move to next state
    await state.set_state(NewsletterState.button)
    
    await message.answer(
        f"File attached! Now you can add a button with a link to your newsletter (optional).\n\n"
        f"If you want to add a button, send the button text and URL in this format:\n"
        f"{hcode('Button Text | https://example.com')}\n\n"
        f"Or click 'Skip Button' to continue without a button:",
        reply_markup=get_newsletter_button_keyboard()
    )

async def skip_newsletter_file(callback: CallbackQuery, state: FSMContext):
    """Skip adding a file to the newsletter"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return
    
    # Save null file info to state
    await state.update_data(file_id=None, file_name=None)
    
    # Move to next state
    await state.set_state(NewsletterState.button)
    
    await callback.message.answer(
        f"File attachment skipped. Now you can add a button with a link to your newsletter (optional).\n\n"
        f"If you want to add a button, send the button text and URL in this format:\n"
        f"{hcode('Button Text | https://example.com')}\n\n"
        f"Or click 'Skip Button' to continue without a button:",
        reply_markup=get_newsletter_button_keyboard()
    )
    await callback.answer()

async def process_newsletter_button(message: Message, state: FSMContext):
    """Process newsletter button input"""
    if not await is_admin(message.from_user.id):
        await message.answer("Access denied")
        await state.clear()
        return
    
    # Parse button text and URL
    try:
        if '|' not in message.text:
            await message.answer(
                f"Invalid format. Please use format:\n"
                f"{hcode('Button Text | https://example.com')}\n\n"
                f"Or click 'Skip Button' to continue without a button."
            )
            return
        
        parts = message.text.split('|', 1)
        button_text = parts[0].strip()
        button_url = parts[1].strip()
        
        # Validate button text length
        if len(button_text) > 100:
            await message.answer(
                "Button text is too long (max 100 characters). Please enter a shorter text:"
            )
            return
        
        # Basic URL validation
        if not button_url.startswith(('http://', 'https://')):
            await message.answer(
                "Invalid URL. URL must start with http:// or https://. Please try again:"
            )
            return
        
        # Save button info to state
        await state.update_data(button_text=button_text, button_url=button_url)
        
        # Show button preview
        await message.answer(
            f"Button added! Preview:",
            reply_markup=get_newsletter_button_preview(button_text, button_url)
        )
        
        # Move to preview state
        await show_newsletter_preview(message, state)
    except Exception as e:
        logger.error(f"Error processing newsletter button: {e}")
        await message.answer(
            f"Error processing button. Please try again with format:\n"
            f"{hcode('Button Text | https://example.com')}"
        )

# todo: Fix save and notify newsletter maybe DB

async def skip_newsletter_button(callback: CallbackQuery, state: FSMContext):
    """Skip adding a button to the newsletter"""

    if not await is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return
    
    # Save null button info to state
    await state.update_data(button_text=None, button_url=None)
    
    # Move to preview state
    await callback.answer()
    await show_newsletter_preview(callback.message, state)

async def show_newsletter_preview(message: Message, state: FSMContext):
    """Show preview of the newsletter before saving/sending"""
    if not await is_admin(message.chat.id):
        
        await message.answer("Access denied")
        await state.clear()
        return
    
    # Set preview state
    await state.set_state(NewsletterState.preview)
    
    # Get all data from state
    data = await state.get_data()
    
    # Get estimated recipient count
    recipients = await get_all_users_telegram_ids()
    recipient_count = len(recipients)
    
    # Format button info
    button_text = ""
    if data.get('button_text') and data.get('button_url'):
        button_text = f"\n\n{hbold('Button:')}\nText: {data['button_text']}\nURL: {data['button_url']}"
    
    # Format file info
    file_text = ""
    if data.get('file_name'):
        file_text = f"\n\n{hbold('Attached File:')}\n{data['file_name']}"
    
    # Format preview
    preview_text = (
        f"📨 {hbold('Newsletter Preview')}\n\n"
        f"{hbold('Title:')}\n{data.get('title')}\n\n"
        f"{hbold('Message:')}\n{data.get('message_text')}"
        f"{button_text}"
        f"{file_text}\n\n"
        f"{hbold('Recipients:')}\nThis newsletter will be sent to approximately {recipient_count} users."
    )
    
    # If there's a photo, show it
    if data.get('photo_id'):
        try:
            await message.answer_photo(
                photo=data['photo_id'],
                caption=preview_text,
                reply_markup=get_newsletter_preview_keyboard()
            )
        except Exception as e:
            logger.error(f"Error showing newsletter photo preview: {e}")
            # If photo preview fails, just show as text
            await message.answer(
                f"Note: Unable to display photo preview.\n\n{preview_text}",
                reply_markup=get_newsletter_preview_keyboard()
            )
    else:
        # No photo, just show text
        await message.answer(
            preview_text,
            reply_markup=get_newsletter_preview_keyboard()
        )

async def edit_newsletter_field(callback: CallbackQuery, state: FSMContext):
    """Handle editing a specific field of the newsletter"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return
    
    # Extract field to edit from callback data
    field = callback.data.split('_')[2]
    
    if field == "title":
        await state.set_state(NewsletterState.title)
        await callback.message.answer("Please enter the new title for your newsletter:")
    elif field == "message":
        await state.set_state(NewsletterState.message_text)
        await callback.message.answer(
            "Please enter the new message text for your newsletter:\n\n"
            "Note: HTML formatting is supported."
        )
    elif field == "photo":
        await state.set_state(NewsletterState.photo)
        await callback.message.answer(
            "Please send a new photo for your newsletter or click 'Skip Photo' to remove the current photo:",
            reply_markup=get_newsletter_photo_keyboard()
        )
    elif field == "file":
        await state.set_state(NewsletterState.file)
        await callback.message.answer(
            "Please send a new file for your newsletter or click 'Skip File Attachment' to remove the current file:",
            reply_markup=get_newsletter_file_keyboard()
        )
    elif field == "button":
        await state.set_state(NewsletterState.button)
        await callback.message.answer(
            f"Please enter the new button text and URL in this format:\n"
            f"{hcode('Button Text | https://example.com')}\n\n"
            f"Or click 'Skip Button' to remove the current button:",
            reply_markup=get_newsletter_button_keyboard()
        )
    
    await callback.answer()

async def save_newsletter_draft(callback: CallbackQuery, state: FSMContext):
    """Save newsletter as draft without sending"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return
    
    # Get all data from state
    data = await state.get_data()
    
    # Create newsletter with user ID
    newsletter = await create_newsletter(data, callback.from_user.id)
    
    if newsletter:
        await callback.message.answer(
            f"✅ Newsletter '{newsletter.title}' has been saved as a draft.\n\n"
            f"You can view and send it later from the 'My Newsletters' section.",
            reply_markup=get_newsletter_main_keyboard()
        )
    else:
        await callback.message.answer(
            "❌ Failed to save newsletter. Please try again.",
            reply_markup=get_newsletter_main_keyboard()
        )
    
    # Clear state
    await state.clear()
    await callback.answer()

async def confirm_send_newsletter(callback: CallbackQuery, state: FSMContext):
    """Confirm sending the newsletter to all users"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return
    
    # Get recipients count
    recipients = await get_all_users_telegram_ids()
    recipient_count = len(recipients)
    
    # Set confirm state
    await state.set_state(NewsletterState.confirm)
    
    await callback.message.answer(
        f"⚠️ {hbold('Confirm Send')}\n\n"
        f"You are about to send this newsletter to {hbold(str(recipient_count))} users.\n\n"
        f"Are you sure you want to proceed?\n\n"
        f"Reply with {hcode('yes')} to confirm or {hcode('no')} to cancel."
    )
    await callback.answer()

async def process_send_confirmation(message: Message, state: FSMContext):
    """Process the confirmation to send the newsletter"""
    if not await is_admin(message.from_user.id):
        await message.answer("Access denied")
        await state.clear()
        return
    
    # Check confirmation
    if message.text.lower() != 'yes':
        await message.answer(
            "Newsletter sending cancelled.",
            reply_markup=get_newsletter_main_keyboard()
        )
        await state.clear()
        return
    
    # Get all data from state
    data = await state.get_data()
    
    # Create newsletter with user ID
    newsletter = await create_newsletter(data, message.from_user.id)
    
    if not newsletter:
        await message.answer(
            "❌ Failed to create newsletter. Please try again.",
            reply_markup=get_newsletter_main_keyboard()
        )
        await state.clear()
        return
    
    # Get all users
    user_ids = await get_all_users_telegram_ids()
    total_users = len(user_ids)
    
    # Send status message
    status_message = await message.answer(
        f"🚀 {hbold('Sending Newsletter')}\n\n"
        f"Newsletter: {newsletter.title}\n"
        f"Recipients: {total_users}\n\n"
        f"Status: Sending... 0%"
    )
    
    # Start sending process
    await send_newsletter_to_users(message.bot, newsletter.id, user_ids, status_message)
    
    # Clear state
    await state.clear()

async def send_newsletter_to_users(bot: Bot, newsletter_id: int, user_ids: list, status_message: Message):
    """Send the newsletter to all users with progress updates"""
    # Get newsletter details
    newsletter = await get_newsletter(newsletter_id)
    
    if not newsletter:
        await status_message.edit_text(
            "❌ Failed to send newsletter. Newsletter not found."
        )
        return
    
    # Update newsletter status
    await update_newsletter(newsletter_id, {"status": "sending"})
    
    total_users = len(user_ids)
    success_count = 0
    error_count = 0
    batch_size = 25  # Send to 25 users at a time
    update_interval = max(1, total_users // 20)  # Update status every 5% of progress
    last_update = 0
    
    # Create keyboard with button if specified
    inline_keyboard = None
    if newsletter.button_text and newsletter.button_url:
        inline_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(text=newsletter.button_text, url=newsletter.button_url)
            ]]
        )
    
    start_time = time.time()
    
    # Process users in batches
    for i in range(0, total_users, batch_size):
        batch = user_ids[i:i+batch_size]
        batch_tasks = []
        
        for user_id in batch:
            # Create task for sending message to user
            task = send_to_user(
                bot, 
                user_id, 
                newsletter, 
                inline_keyboard
            )
            batch_tasks.append(task)
        
        # Run batch of tasks
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        # Count successes and errors
        for result in batch_results:
            if isinstance(result, Exception):
                error_count += 1
                logger.error(f"Error sending newsletter: {result}")
            else:
                success_count += 1
        
        # Update progress periodically
        current_progress = i + len(batch)
        if current_progress - last_update >= update_interval or current_progress >= total_users:
            progress_percent = min(100, int((current_progress / total_users) * 100))
            await status_message.edit_text(
                f"🚀 {hbold('Sending Newsletter')}\n\n"
                f"Newsletter: {newsletter.title}\n"
                f"Recipients: {total_users}\n"
                f"Progress: {current_progress}/{total_users} ({progress_percent}%)\n"
                f"Successful: {success_count}\n"
                f"Failed: {error_count}"
            )
            last_update = current_progress
        
        # Add a small delay between batches to avoid rate limits
        await asyncio.sleep(0.5)
    
    end_time = time.time()
    send_time = end_time - start_time
    
    # Update newsletter with statistics
    stats = {
        "status": "sent",
        "sent_at": datetime.utcnow(),
        "recipients_count": total_users,
        "success_count": success_count,
        "error_count": error_count,
        "send_time": send_time
    }
    
    await mark_newsletter_as_sent(newsletter_id, stats)
    
    # Show final status
    await status_message.edit_text(
        f"✅ {hbold('Newsletter Sent')}\n\n"
        f"Newsletter: {newsletter.title}\n\n"
        f"{hbold('Results:')}\n"
        f"• Total recipients: {total_users}\n"
        f"• Successfully sent: {success_count}\n"
        f"• Failed: {error_count}\n"
        f"• Completion time: {send_time:.1f} seconds"
    )

async def send_to_user(bot: Bot, user_id: int, newsletter, inline_keyboard=None):
    """Send newsletter to a specific user"""
    try:
        # If there's a photo, send with photo
        if newsletter.photo_id:
            await bot.send_photo(
                chat_id=user_id,
                photo=newsletter.photo_id,
                caption=newsletter.message_text,
                reply_markup=inline_keyboard,
                parse_mode="HTML"
            )
        
        # If there's a file, send it after the main message
        elif newsletter.file_id:
            # Send message first
            await bot.send_message(
                chat_id=user_id,
                text=newsletter.message_text,
                reply_markup=inline_keyboard,
                parse_mode="HTML"
            )
            
            # Then send file
            await bot.send_document(
                chat_id=user_id,
                document=newsletter.file_id,
                caption=f"Attachment for: {newsletter.title}",
                parse_mode="HTML"
            )
        
        # Otherwise just send text
        else:
            await bot.send_message(
                chat_id=user_id,
                text=newsletter.message_text,
                reply_markup=inline_keyboard,
                parse_mode="HTML"
            )
        
        return True
    except Exception as e:
        logger.error(f"Error sending newsletter to user {user_id}: {e}")
        return e

async def send_existing_newsletter(callback: CallbackQuery):
    """Send a previously created newsletter"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return
    
    # Extract newsletter ID from callback data (send_newsletter:123)
    newsletter_id = int(callback.data.split(':')[1])
    
    # Get newsletter details
    newsletter = await get_newsletter(newsletter_id)
    
    if not newsletter:
        await callback.answer("Newsletter not found.", show_alert=True)
        return
    
    # Check if already sent
    if newsletter.status == "sent":
        await callback.answer("This newsletter has already been sent.", show_alert=True)
        return
    
    # Get all users
    user_ids = await get_all_users_telegram_ids()
    total_users = len(user_ids)
    
    # Confirm sending
    await callback.message.answer(
        f"⚠️ {hbold('Confirm Send')}\n\n"
        f"You are about to send newsletter '{newsletter.title}' to {hbold(str(total_users))} users.\n\n"
        f"Are you sure you want to proceed?\n\n"
        f"Reply with {hcode('yes')} to confirm or {hcode('no')} to cancel.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(
                    text="✅ Yes, Send Now",
                    callback_data=f"confirm_send_existing:{newsletter_id}"
                )
            ], [
                InlineKeyboardButton(
                    text="❌ No, Cancel",
                    callback_data=f"view_newsletter:{newsletter_id}"
                )
            ]]
        )
    )
    await callback.answer()

async def confirm_send_existing_newsletter(callback: CallbackQuery):
    """Confirm sending an existing newsletter"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return
    
    # Extract newsletter ID from callback data
    newsletter_id = int(callback.data.split(':')[1])
    
    # Get newsletter details
    newsletter = await get_newsletter(newsletter_id)
    
    if not newsletter:
        await callback.answer("Newsletter not found.", show_alert=True)
        return
    
    # Get all users
    user_ids = await get_all_users_telegram_ids()
    total_users = len(user_ids)
    
    # Send status message
    status_message = await callback.message.answer(
        f"🚀 {hbold('Sending Newsletter')}\n\n"
        f"Newsletter: {newsletter.title}\n"
        f"Recipients: {total_users}\n\n"
        f"Status: Sending... 0%"
    )
    
    # Start sending process
    await send_newsletter_to_users(callback.bot, newsletter.id, user_ids, status_message)
    await callback.answer()

async def delete_newsletter_request(callback: CallbackQuery):
    """Request confirmation to delete a newsletter"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return
    
    # Extract newsletter ID from callback data (delete_newsletter:123)
    newsletter_id = int(callback.data.split(':')[1])
    
    # Get newsletter details
    newsletter = await get_newsletter(newsletter_id)
    
    if not newsletter:
        await callback.answer("Newsletter not found.", show_alert=True)
        return
    
    await callback.message.answer(
        f"⚠️ {hbold('Confirm Delete')}\n\n"
        f"You are about to delete the newsletter: {hbold(newsletter.title)}\n\n"
        f"This action cannot be undone. Are you sure?",
        reply_markup=get_newsletter_confirm_delete_keyboard(newsletter_id)
    )
    await callback.answer()

async def confirm_delete_newsletter(callback: CallbackQuery):
    """Confirm and delete a newsletter"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return
    
    # Extract newsletter ID from callback data (confirm_delete_newsletter:123)
    newsletter_id = int(callback.data.split(':')[1])
    
    # Delete newsletter
    success = await delete_newsletter(newsletter_id)
    
    if success:
        await callback.message.answer(
            "✅ Newsletter has been successfully deleted!",
            reply_markup=get_newsletter_main_keyboard()
        )
    else:
        await callback.message.answer(
            "❌ Failed to delete newsletter. Please try again.",
            reply_markup=get_newsletter_main_keyboard()
        )
    
    await callback.answer()

async def cancel_newsletter(callback: CallbackQuery, state: FSMContext):
    """Cancel newsletter creation process"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("Access denied", show_alert=True)
        return
    
    # Clear state
    await state.clear()
    
    await callback.message.answer(
        "Newsletter creation cancelled.",
        reply_markup=get_newsletter_main_keyboard()
    )
    await callback.answer()

def register_newsletter_handlers(dp: Dispatcher):
    """Register newsletter handlers"""
    # Main menu
    dp.callback_query.register(show_newsletter_menu, F.data == "admin_newsletter")
    dp.callback_query.register(show_my_newsletters, F.data == "my_newsletters")
    dp.callback_query.register(paginate_newsletters, F.data.startswith("newsletter_page:"))
    
    # View and manage newsletters
    dp.callback_query.register(view_newsletter, F.data.startswith("view_newsletter:"))
    dp.callback_query.register(send_existing_newsletter, F.data.startswith("send_newsletter:"))
    dp.callback_query.register(confirm_send_existing_newsletter, F.data.startswith("confirm_send_existing:"))
    dp.callback_query.register(delete_newsletter_request, F.data.startswith("delete_newsletter:"))
    dp.callback_query.register(confirm_delete_newsletter, F.data.startswith("confirm_delete_newsletter:"))
    
    # Create new newsletter
    dp.callback_query.register(start_create_newsletter, F.data == "create_newsletter")
    dp.message.register(process_newsletter_title, NewsletterState.title)
    dp.message.register(process_newsletter_message, NewsletterState.message_text)
    dp.message.register(process_newsletter_photo, NewsletterState.photo)
    dp.callback_query.register(skip_newsletter_photo, F.data == "skip_newsletter_photo")
    dp.message.register(process_newsletter_file, NewsletterState.file)
    dp.callback_query.register(skip_newsletter_file, F.data == "skip_newsletter_file")
    dp.message.register(process_newsletter_button, NewsletterState.button)
    dp.callback_query.register(skip_newsletter_button, F.data == "skip_newsletter_button")
    
    # Preview and edit
    dp.callback_query.register(edit_newsletter_field, F.data.startswith("edit_newsletter_"))
    dp.callback_query.register(save_newsletter_draft, F.data == "save_newsletter_draft")
    dp.callback_query.register(confirm_send_newsletter, F.data == "confirm_send_newsletter")
    dp.message.register(process_send_confirmation, NewsletterState.confirm)
    
    # Cancel
    dp.callback_query.register(cancel_newsletter, F.data == "cancel_newsletter")