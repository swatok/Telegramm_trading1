from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class DatabaseInterface(ABC):
    """Інтерфейс для роботи з базою даних"""

    @abstractmethod
    async def connect(self) -> bool:
        """
        Підключення до бази даних

        Returns:
            True якщо підключення успішне, False інакше
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """
        Відключення від бази даних
        """
        pass

    @abstractmethod
    async def save(self, collection: str, data: Dict[str, Any]) -> bool:
        """
        Збереження даних

        Args:
            collection: Назва колекції
            data: Дані для збереження

        Returns:
            True якщо збереження успішне, False інакше
        """
        pass

    @abstractmethod
    async def find(self, collection: str, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Пошук даних

        Args:
            collection: Назва колекції
            query: Параметри пошуку

        Returns:
            Список знайдених документів
        """
        pass

    @abstractmethod
    async def update(self, collection: str, query: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """
        Оновлення даних

        Args:
            collection: Назва колекції
            query: Параметри пошуку
            data: Нові дані

        Returns:
            True якщо оновлення успішне, False інакше
        """
        pass

    @abstractmethod
    async def delete(self, collection: str, query: Dict[str, Any]) -> bool:
        """
        Видалення даних

        Args:
            collection: Назва колекції
            query: Параметри пошуку

        Returns:
            True якщо видалення успішне, False інакше
        """
        pass
