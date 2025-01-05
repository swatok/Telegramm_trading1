from typing import Optional, Dict, Any
import asyncio
from datetime import datetime
from telethon import TelegramClient

from utils import get_logger
from utils.decorators import log_execution
from .config_manager import ConfigManager

logger = get_logger("notification_manager")

class NotificationManager:
    def __init__(
        self,
        bot_client: TelegramClient,
        config_manager: ConfigManager
    ):
        """
        Ініціалізація менеджера сповіщень
        
        Args:
            bot_client: Клієнт для відправки сповіщень
            config_manager: Менеджер конфігурації
        """
        self.bot_client = bot_client
        self.config = config_manager
        
    @log_execution
    async def send_notification(
        self,
        message: str,
        notification_type: str = "info",
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Відправка сповіщення
        
        Args:
            message: Текст сповіщення
            notification_type: Тип сповіщення (info, warning, error)
            data: Додаткові дані
        """
        try:
            # Отримуємо ID адміністратора
            admin_id = self.config.get('ADMIN_ID')
            if not admin_id:
                logger.error("Не налаштовано ID адміністратора")
                return
                
            # Форматуємо повідомлення
            formatted_message = self._format_message(message, notification_type, data)
            
            # Відправляємо сповіщення
            await self.bot_client.send_message(admin_id, formatted_message)
            logger.info(f"Відправлено сповіщення типу {notification_type}")
            
        except Exception as e:
            logger.error(f"Помилка відправки сповіщення: {e}")
            
    @log_execution
    async def send_error_notification(
        self,
        error_message: str,
        error_type: str,
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Відправка сповіщення про помилку
        
        Args:
            error_message: Текст помилки
            error_type: Тип помилки
            data: Додаткові дані
        """
        try:
            # Форматуємо повідомлення про помилку
            message = (
                f"❌ Помилка: {error_type}\n"
                f"📝 Опис: {error_message}\n"
            )
            
            if data:
                message += "\n🔍 Деталі:\n"
                for key, value in data.items():
                    message += f"{key}: {value}\n"
                    
            # Відправляємо сповіщення
            await self.send_notification(message, "error", data)
            
        except Exception as e:
            logger.error(f"Помилка відправки сповіщення про помилку: {e}")
            
    @log_execution
    async def send_trade_notification(
        self,
        trade_type: str,
        token_symbol: str,
        price: float,
        amount: float,
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Відправка сповіщення про торгівлю
        
        Args:
            trade_type: Тип торгівлі (buy/sell)
            token_symbol: Символ токена
            price: Ціна
            amount: Кількість
            data: Додаткові дані
        """
        try:
            # Форматуємо повідомлення про торгівлю
            emoji = "🟢" if trade_type.lower() == "buy" else "🔴"
            message = (
                f"{emoji} {trade_type.upper()}\n\n"
                f"Токен: {token_symbol}\n"
                f"Ціна: {price}\n"
                f"Кількість: {amount}\n"
            )
            
            if data:
                message += "\n📊 Деталі:\n"
                for key, value in data.items():
                    message += f"{key}: {value}\n"
                    
            # Відправляємо сповіщення
            await self.send_notification(message, "trade", data)
            
        except Exception as e:
            logger.error(f"Помилка відправки сповіщення про торгівлю: {e}")
            
    @log_execution
    async def send_position_notification(
        self,
        position_id: int,
        token_symbol: str,
        position_type: str,
        entry_price: float,
        current_price: float,
        pnl: float,
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Відправка сповіщення про позицію
        
        Args:
            position_id: ID позиції
            token_symbol: Символ токена
            position_type: Тип позиції
            entry_price: Ціна входу
            current_price: Поточна ціна
            pnl: Прибуток/збиток
            data: Додаткові дані
        """
        try:
            # Форматуємо повідомлення про позицію
            emoji = "📈" if pnl >= 0 else "📉"
            message = (
                f"{emoji} Позиція #{position_id}\n\n"
                f"Токен: {token_symbol}\n"
                f"Тип: {position_type}\n"
                f"Ціна входу: {entry_price}\n"
                f"Поточна ціна: {current_price}\n"
                f"P&L: {pnl}%\n"
            )
            
            if data:
                message += "\n📊 Деталі:\n"
                for key, value in data.items():
                    message += f"{key}: {value}\n"
                    
            # Відправляємо сповіщення
            await self.send_notification(message, "position", data)
            
        except Exception as e:
            logger.error(f"Помилка відправки сповіщення про позицію: {e}")
            
    @log_execution
    async def send_system_notification(
        self,
        event_type: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Відправка системного сповіщення
        
        Args:
            event_type: Тип події
            message: Текст сповіщення
            data: Додаткові дані
        """
        try:
            # Форматуємо системне повідомлення
            formatted_message = (
                f"🔧 Системна подія: {event_type}\n\n"
                f"{message}\n"
            )
            
            if data:
                formatted_message += "\n📊 Деталі:\n"
                for key, value in data.items():
                    formatted_message += f"{key}: {value}\n"
                    
            # Відправляємо сповіщення
            await self.send_notification(formatted_message, "system", data)
            
        except Exception as e:
            logger.error(f"Помилка відправки системного сповіщення: {e}")
            
    def _format_message(
        self,
        message: str,
        notification_type: str,
        data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Форматування повідомлення
        
        Args:
            message: Текст повідомлення
            notification_type: Тип сповіщення
            data: Додаткові дані
            
        Returns:
            str: Відформатоване повідомлення
        """
        # Додаємо часову мітку
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Вибираємо емодзі в залежності від типу
        type_emoji = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "trade": "💱",
            "position": "📊",
            "system": "🔧"
        }.get(notification_type, "📝")
        
        # Форматуємо повідомлення
        formatted_message = (
            f"{type_emoji} {message}\n\n"
            f"🕒 {timestamp}"
        )
        
        return formatted_message
