import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import load_config
from handlers import register_handlers
from middlewares.middleware import setup_middlewares
from database.methods import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

async def main():
    # Load configuration
    config = load_config()
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Initialize Bot and Dispatcher with updated syntax for aiogram 3.7.0+
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())
    
    # Setup middlewares
    setup_middlewares(dp)
    
    # Register all handlers
    register_handlers(dp)
    
    # Start the bot
    logger.info("Starting bot")
    
    # Delete webhook before polling
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Start polling
    try:
        await dp.start_polling(bot)
    finally:
        await dp.storage.close()
        await bot.session.close()
        logger.info("Bot stopped")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")