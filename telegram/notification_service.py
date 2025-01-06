from typing import Optional, List
from aiogram import Bot
from aiogram.types import Message

from interfaces.telegram_interfaces import BaseService

class NotificationService(BaseService):
    """Service for sending notifications to users"""
    
    def __init__(self, token: str, notification_chat_ids: List[int]):
        """Initialize notification service"""
        self.bot = Bot(token=token)
        self.notification_chat_ids = notification_chat_ids
    
    async def start(self) -> None:
        """Start the service"""
        # Nothing to start for notification service
        pass
    
    async def stop(self) -> None:
        """Stop the service"""
        await self.bot.close()
    
    async def send_message(self, chat_id: int, text: str) -> Optional[Message]:
        """Send message to specified chat"""
        try:
            return await self.bot.send_message(chat_id=chat_id, text=text)
        except Exception as e:
            print(f"Error sending message: {e}")
            return None
    
    async def broadcast(self, text: str) -> List[Optional[Message]]:
        """Send message to all notification chats"""
        messages = []
        for chat_id in self.notification_chat_ids:
            message = await self.send_message(chat_id, text)
            messages.append(message)
        return messages
    
    async def notify_position_opened(self, position_id: int, token: str, amount: float, price: float) -> None:
        """Send notification about opened position"""
        text = (
            "📈 Відкрито нову позицію:\n"
            f"ID: {position_id}\n"
            f"Токен: {token}\n"
            f"Кількість: {amount}\n"
            f"Ціна: {price}"
        )
        await self.broadcast(text)
    
    async def notify_position_closed(self, position_id: int, profit: float) -> None:
        """Send notification about closed position"""
        text = (
            "📉 Закрито позицію:\n"
            f"ID: {position_id}\n"
            f"Прибуток: {profit}"
        )
        await self.broadcast(text)
    
    async def notify_error(self, error_message: str) -> None:
        """Send notification about error"""
        text = f"❌ Помилка: {error_message}"
        await self.broadcast(text)
    
    async def notify_balance_update(self, new_balance: float) -> None:
        """Send notification about balance update"""
        text = f"💰 Оновлення балансу: {new_balance}"
        await self.broadcast(text) 