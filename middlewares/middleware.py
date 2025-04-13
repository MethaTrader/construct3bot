import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware, Dispatcher
from aiogram.types import Message, TelegramObject

# Logger
logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseMiddleware):
    """Simple middleware to log all incoming messages"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Log incoming message if it's a Message object
        if isinstance(event, Message) and event.text:
            logger.info(f"Received message from {event.from_user.id}: {event.text}")
        
        # Process the event through handler
        return await handler(event, data)


def setup_middlewares(dp: Dispatcher):
    """Setup all middlewares"""
    # Добавьте ручной лог, чтобы проверить, что функция вызывается
    logger.info("Setting up middlewares...")

    # Register logging middleware
    dp.message.middleware(LoggingMiddleware())

    logger.info("Middlewares setup complete")