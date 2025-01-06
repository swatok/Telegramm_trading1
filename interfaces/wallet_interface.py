from abc import ABC, abstractmethod
from typing import Dict, Any

class WalletInterface(ABC):
    """Інтерфейс для управління гаманцем"""

    @abstractmethod
    async def check_balance(self, token: str) -> float:
        """
        Перевірка балансу

        Args:
            token: Токен для перевірки балансу

        Returns:
            Баланс токену
        """
        pass

    @abstractmethod
    async def deposit(self, token: str, amount: float) -> bool:
        """
        Поповнення гаманця

        Args:
            token: Токен для поповнення
            amount: Сума поповнення

        Returns:
            True якщо поповнення успішне, False інакше
        """
        pass

    @abstractmethod
    async def withdraw(self, token: str, amount: float) -> bool:
        """
        Зняття коштів з гаманця

        Args:
            token: Токен для зняття
            amount: Сума зняття

        Returns:
            True якщо зняття успішне, False інакше
        """
        pass 