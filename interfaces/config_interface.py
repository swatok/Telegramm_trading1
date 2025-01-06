from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class ConfigInterface(ABC):
    """Інтерфейс для роботи з конфігурацією"""

    @abstractmethod
    async def load(self, config_path: str) -> bool:
        """
        Завантаження конфігурації

        Args:
            config_path: Шлях до файлу конфігурації

        Returns:
            True якщо завантаження успішне, False інакше
        """
        pass

    @abstractmethod
    async def get(self, key: str, default: Any = None) -> Any:
        """
        Отримання значення з конфігурації

        Args:
            key: Ключ конфігурації
            default: Значення за замовчуванням

        Returns:
            Значення з конфігурації
        """
        pass

    @abstractmethod
    async def set(self, key: str, value: Any) -> bool:
        """
        Встановлення значення в конфігурації

        Args:
            key: Ключ конфігурації
            value: Нове значення

        Returns:
            True якщо встановлення успішне, False інакше
        """
        pass

    @abstractmethod
    async def save(self) -> bool:
        """
        Збереження конфігурації

        Returns:
            True якщо збереження успішне, False інакше
        """
        pass 