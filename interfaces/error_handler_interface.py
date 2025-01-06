"""Інтерфейс для обробки помилок"""

from abc import ABC, abstractmethod
from typing import Optional, Any, Dict

class ErrorHandlerInterface(ABC):
    """Базовий інтерфейс для обробки помилок"""
    
    @abstractmethod
    async def handle_error(
        self,
        message: str,
        error: Exception,
        critical: bool = False,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Обробка помилки
        
        Args:
            message: Повідомлення про помилку
            error: Об'єкт помилки
            critical: Чи є помилка критичною
            context: Додатковий контекст помилки
        """
        pass
        
    @abstractmethod
    async def handle_warning(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Обробка попередження
        
        Args:
            message: Текст попередження
            context: Додатковий контекст
        """
        pass
        
    @abstractmethod
    def format_error_message(
        self,
        error_details: Dict[str, Any]
    ) -> str:
        """
        Форматування повідомлення про помилку
        
        Args:
            error_details: Деталі помилки
            
        Returns:
            Відформатоване повідомлення
        """
        pass 