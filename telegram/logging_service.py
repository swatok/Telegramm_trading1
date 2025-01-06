import logging
import asyncio
from typing import Optional, List
from datetime import datetime

from aiogram import Bot
from aiogram.types import Message

from interfaces.telegram_interfaces import BaseService

class TelegramHandler(logging.Handler):
    """Custom logging handler that sends logs to Telegram"""
    
    def __init__(self, service: 'LoggingService'):
        """Initialize handler with logging service"""
        super().__init__()
        self.service = service
        
        # Set formatter
        formatter = logging.Formatter(
            "📝 %(levelname)s [%(asctime)s]\n"
            "📂 %(name)s\n"
            "📍 %(funcName)s:%(lineno)d\n"
            "📄 %(message)s"
        )
        self.setFormatter(formatter)
    
    def emit(self, record: logging.LogRecord) -> None:
        """Send log record to Telegram"""
        try:
            msg = self.format(record)
            asyncio.create_task(self.service.broadcast(msg))
        except Exception as e:
            print(f"Error sending log to Telegram: {e}")

class LoggingService(BaseService):
    """Service for sending logs to Telegram"""
    
    def __init__(self, token: str, logging_chat_ids: List[int], min_level: int = logging.INFO):
        """Initialize logging service"""
        self.bot = Bot(token=token)
        self.logging_chat_ids = logging_chat_ids
        
        # Create handler
        self.handler = TelegramHandler(self)
        self.handler.setLevel(min_level)
        
        # Get root logger
        self.logger = logging.getLogger()
        self.logger.addHandler(self.handler)
    
    async def start(self) -> None:
        """Start logging service"""
        startup_message = (
            "🚀 Логування запущено\n"
            f"🕒 Час: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"📊 Мінімальний рівень: {logging.getLevelName(self.handler.level)}"
        )
        await self.broadcast(startup_message)
    
    async def stop(self) -> None:
        """Stop logging service"""
        # Remove handler from root logger
        self.logger.removeHandler(self.handler)
        
        # Send shutdown message
        shutdown_message = (
            "🛑 Логування зупинено\n"
            f"🕒 Час: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        await self.broadcast(shutdown_message)
        
        # Close bot
        await self.bot.close()
    
    async def send_message(self, chat_id: int, text: str) -> Optional[Message]:
        """Send message to specified chat"""
        try:
            return await self.bot.send_message(chat_id=chat_id, text=text)
        except Exception as e:
            print(f"Error sending message: {e}")
            return None
    
    async def broadcast(self, text: str) -> List[Optional[Message]]:
        """Send message to all logging chats"""
        messages = []
        for chat_id in self.logging_chat_ids:
            message = await self.send_message(chat_id, text)
            messages.append(message)
        return messages 