import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import load_config
from handlers import register_handlers
from middlewares.middleware import setup_middlewares
from database.methods import init_db, config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # Явно добавляем вывод в консоль
        logging.FileHandler("bot.log")  # Можно также сохранять логи в файл
    ]
)
logger = logging.getLogger(__name__)


async def apply_migrations():
    """Apply database migrations using subprocess with timeout"""
    try:
        logger.info("Starting database migrations")
        import subprocess
        import sys
        import os

        # Получение абсолютного пути к директории проекта
        base_path = os.path.dirname(os.path.abspath(__file__))

        # Убедитесь, что директория для базы данных существует
        data_dir = os.path.join(base_path, "data")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            logger.info(f"Created data directory: {data_dir}")

        # Запуск миграций в отдельном процессе с таймаутом
        logger.info("Running alembic as subprocess")
        try:
            # Создаем переменные окружения для subprocess
            env = os.environ.copy()
            # Добавляем PYTHONPATH чтобы убедиться, что импорты работают
            env["PYTHONPATH"] = base_path

            result = subprocess.run(
                [sys.executable, "-m", "alembic", "upgrade", "head"],
                cwd=base_path,
                capture_output=True,
                text=True,
                timeout=15,  # Таймаут 15 секунд
                env=env
            )

            if result.returncode == 0:
                logger.info("Database migrations applied successfully")
                if result.stdout:
                    logger.info(f"Migration output: {result.stdout}")
            else:
                logger.error(f"Migration failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            logger.error("Migration subprocess timed out after 15 seconds")

    except Exception as e:
        logger.error(f"Error in migration process: {e}")

async def main():
    # Load configuration
    config = load_config()

    logger.info("Starting bot initialization")

    # Apply migrations
    await apply_migrations()

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