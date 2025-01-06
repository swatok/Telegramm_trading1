from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class StrategyInterface(ABC):
    """Інтерфейс для роботи з торговими стратегіями"""

    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Ініціалізація стратегії

        Args:
            config: Конфігурація стратегії

        Returns:
            True якщо ініціалізація успішна, False інакше
        """
        pass

    @abstractmethod
    async def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Аналіз ринкових даних

        Args:
            market_data: Ринкові дані для аналізу

        Returns:
            Результат аналізу
        """
        pass

    @abstractmethod
    async def generate_signal(self, analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Генерація торгового сигналу

        Args:
            analysis: Результат аналізу ринку

        Returns:
            Торговий сигнал або None якщо сигнал не згенеровано
        """
        pass

    @abstractmethod
    async def validate_signal(self, signal: Dict[str, Any]) -> bool:
        """
        Валідація торгового сигналу

        Args:
            signal: Торговий сигнал для перевірки

        Returns:
            True якщо сигнал валідний, False інакше
        """
        pass 