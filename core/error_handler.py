"""Базовий обробник помилок"""

import traceback
from typing import Optional, Any, Dict
from datetime import datetime

from utils import get_logger
from interfaces.error_handler_interface import ErrorHandlerInterface
from .notification_manager import NotificationManager

logger = get_logger("error_handler")

class BaseErrorHandler(ErrorHandlerInterface):
    """Базовий клас для обробки помилок"""
    
    def __init__(self, notification_manager: NotificationManager):
        """
        Ініціалізація обробника помилок
        
        Args:
            notification_manager: Менеджер сповіщень
        """
        self.notification_manager = notification_manager
        
    async def handle_error(
        self,
        message: str,
        error: Exception,
        critical: bool = False,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Обробка помилки з логуванням та сповіщенням
        
        Args:
            message: Повідомлення про помилку
            error: Об'єкт помилки
            critical: Чи є помилка критичною
            context: Додатковий контекст помилки
        """
        # Формуємо деталі помилки
        error_details = {
            "message": message,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now().isoformat(),
            "critical": critical,
            "context": context or {}
        }
        
        # Логуємо помилку
        if critical:
            logger.critical(f"{message}: {error}", error_details)
        else:
            logger.error(f"{message}: {error}", error_details)
            
        # Формуємо повідомлення для сповіщення
        notification_message = self.format_error_message(error_details)
        
        # Відправляємо сповіщення
        await self.notification_manager.send_notification(
            notification_message,
            critical=critical
        )
        
    def format_error_message(self, error_details: Dict[str, Any]) -> str:
        """
        Форматування повідомлення про помилку для відправки
        
        Args:
            error_details: Деталі помилки
            
        Returns:
            Відформатоване повідомлення
        """
        critical_prefix = "🔴 КРИТИЧНА ПОМИЛКА" if error_details["critical"] else "⚠️ Помилка"
        
        message = f"{critical_prefix}:\n\n"
        message += f"📝 Опис: {error_details['message']}\n"
        message += f"🔍 Тип: {error_details['error_type']}\n"
        message += f"❌ Помилка: {error_details['error_message']}\n"
        
        # Додаємо контекст якщо він є
        if error_details["context"]:
            message += "\n📋 Контекст:\n"
            for key, value in error_details["context"].items():
                message += f"- {key}: {value}\n"
        
        # Додаємо частину стеку викликів
        tb_lines = error_details["traceback"].split("\n")[-3:]
        message += "\n🔍 Останні рядки стеку:\n"
        message += "\n".join(tb_lines)
        
        return message
    
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
        # Логуємо попередження
        logger.warning(message, context)
        
        # Формуємо повідомлення
        warning_message = f"⚠️ Попередження:\n\n"
        warning_message += f"📝 {message}\n"
        
        if context:
            warning_message += "\n📋 Контекст:\n"
            for key, value in context.items():
                warning_message += f"- {key}: {value}\n"
        
        # Відправляємо сповіщення
        await self.notification_manager.send_notification(warning_message)
