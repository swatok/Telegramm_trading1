from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class APIInterface(ABC):
    """Інтерфейс для роботи з зовнішніми API"""

    @abstractmethod
    async def initialize(self, api_key: str, api_secret: str) -> bool:
        """
        Ініціалізація API клієнта

        Args:
            api_key: API ключ
            api_secret: API секрет

        Returns:
            True якщо ініціалізація успішна, False інакше
        """
        pass

    @abstractmethod
    async def get_market_data(self, symbol: str) -> Dict[str, Any]:
        """
        Отримання ринкових даних

        Args:
            symbol: Торгова пара

        Returns:
            Словник з ринковими даними
        """
        pass

    @abstractmethod
    async def place_order(self, symbol: str, side: str, quantity: float, price: Optional[float] = None) -> Dict[str, Any]:
        """
        Розміщення ордеру

        Args:
            symbol: Торгова пара
            side: Сторона (buy/sell)
            quantity: Кількість
            price: Ціна (опціонально для маркет ордерів)

        Returns:
            Інформація про створений ордер
        """
        pass

    @abstractmethod
    async def cancel_order(self, symbol: str, order_id: str) -> bool:
        """
        Відміна ордеру

        Args:
            symbol: Торгова пара
            order_id: ID ордеру

        Returns:
            True якщо відміна успішна, False інакше
        """
        pass
