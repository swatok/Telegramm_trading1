from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class TelegramMonitorInterface(ABC):
    """Інтерфейс для моніторингу Telegram каналів"""

    @abstractmethod
    async def connect_to_channels(self, channel_ids: List[int]) -> bool:
        """
        Підключення до каналів моніторингу

        Args:
            channel_ids: Список ID каналів для моніторингу

        Returns:
            True якщо підключення успішне, False інакше
        """
        pass

    @abstractmethod
    async def parse_message(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Парсинг повідомлення для виявлення смарт-контрактів

        Args:
            message: Текст повідомлення

        Returns:
            Словник з даними контракту або None якщо контракт не знайдено
        """
        pass

    @abstractmethod
    async def validate_contract(self, contract_data: Dict[str, Any]) -> bool:
        """
        Валідація знайденого контракту

        Args:
            contract_data: Дані контракту

        Returns:
            True якщо контракт валідний, False інакше
        """
        pass

    @abstractmethod
    async def start_monitoring(self) -> None:
        """
        Запуск моніторингу каналів
        """
        pass

    @abstractmethod
    async def stop_monitoring(self) -> None:
        """
        Зупинка моніторингу каналів
        """
        pass 