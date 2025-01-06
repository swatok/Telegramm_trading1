from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class NotificationInterface(ABC):
    """Інтерфейс для роботи з сповіщеннями"""

    @abstractmethod
    async def send_notification(self, message: str, level: str = "info", chat_id: Optional[int] = None) -> bool:
        """
        Відправка сповіщення

        Args:
            message: Текст сповіщення
            level: Рівень важливості (info/warning/error)
            chat_id: ID чату для відправки (опціонально)

        Returns:
            True якщо відправка успішна, False інакше
        """
        pass

    @abstractmethod
    async def send_error(self, error: Exception, chat_id: Optional[int] = None) -> bool:
        """
        Відправка повідомлення про помилку

        Args:
            error: Об'єкт помилки
            chat_id: ID чату для відправки (опціонально)

        Returns:
            True якщо відправка успішна, False інакше
        """
        pass

    @abstractmethod
    async def broadcast(self, message: str, level: str = "info") -> bool:
        """
        Масова розсилка сповіщення

        Args:
            message: Текст сповіщення
            level: Рівень важливості (info/warning/error)

        Returns:
            True якщо розсилка успішна, False інакше
        """
        pass 