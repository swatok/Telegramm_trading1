from abc import ABC, abstractmethod
from typing import Optional

from aiogram.types import Message

class BaseService(ABC):
    """Base interface for all Telegram services"""
    
    @abstractmethod
    async def start(self) -> None:
        """Start the service"""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the service"""
        pass
    
    @abstractmethod
    async def send_message(self, chat_id: int, text: str) -> Optional[Message]:
        """Send message to specified chat"""
        pass
