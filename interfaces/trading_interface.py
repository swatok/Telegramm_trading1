from abc import ABC, abstractmethod
from typing import Dict, Any

class TradingInterface(ABC):
    """Інтерфейс для логіки трейдингу"""

    @abstractmethod
    async def process_trade_signal(self, signal: Dict[str, Any]) -> bool:
        """
        Обробка торгового сигналу

        Args:
            signal: Дані сигналу

        Returns:
            True якщо сигнал успішно оброблено, False інакше
        """
        pass

    @abstractmethod
    async def open_position(self, token: str, amount: float, price: float) -> bool:
        """
        Відкриття нової позиції

        Args:
            token: Токен для торгівлі
            amount: Кількість токенів
            price: Ціна входу

        Returns:
            True якщо позиція успішно відкрита, False інакше
        """
        pass

    @abstractmethod
    async def close_position(self, position_id: int) -> bool:
        """
        Закриття позиції

        Args:
            position_id: Ідентифікатор позиції

        Returns:
            True якщо позиція успішно закрита, False інакше
        """
        pass

    @abstractmethod
    async def get_position_status(self, position_id: int) -> Dict[str, Any]:
        """
        Запит статусу позиції

        Args:
            position_id: Ідентифікатор позиції

        Returns:
            Словник з інформацією про статус позиції
        """
        pass
