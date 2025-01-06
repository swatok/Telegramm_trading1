from abc import ABC, abstractmethod
from typing import Dict, Any

class MonitoringInterface(ABC):
    """Інтерфейс для моніторингу системи"""

    @abstractmethod
    async def monitor_system(self) -> Dict[str, Any]:
        """
        Моніторинг системи

        Returns:
            Словник з інформацією про стан системи
        """
        pass

    @abstractmethod
    async def alert(self, message: str) -> None:
        """
        Відправка сповіщення

        Args:
            message: Повідомлення для сповіщення
        """
        pass
