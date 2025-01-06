from abc import ABC, abstractmethod
from typing import Any, Optional

class LoggingInterface(ABC):
    """Інтерфейс для роботи з логуванням"""

    @abstractmethod
    async def setup(self, log_level: str, log_file: Optional[str] = None) -> bool:
        """
        Налаштування логування

        Args:
            log_level: Рівень логування
            log_file: Шлях до файлу логів (опціонально)

        Returns:
            True якщо налаштування успішне, False інакше
        """
        pass

    @abstractmethod
    async def log(self, message: str, level: str = "info", **kwargs: Any) -> None:
        """
        Запис логу

        Args:
            message: Повідомлення для логування
            level: Рівень логування
            **kwargs: Додаткові параметри для логування
        """
        pass

    @abstractmethod
    async def get_logs(self, level: Optional[str] = None, limit: int = 100) -> list[str]:
        """
        Отримання логів

        Args:
            level: Фільтр за рівнем логування (опціонально)
            limit: Максимальна кількість логів

        Returns:
            Список логів
        """
        pass 