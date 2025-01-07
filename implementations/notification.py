from typing import Dict, Any, Optional, List
import aiohttp
import json
from datetime import datetime
from interfaces.notification_interface import NotificationInterface

class NotificationImplementation(NotificationInterface):
    """Імплементація для відправки сповіщень"""
    
    def __init__(self):
        """Ініціалізація системи сповіщень"""
        self.config = {}
        self.session = None
        self.notification_queue = []
        self.max_queue_size = 1000
        
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Ініціалізація з конфігурацією"""
        try:
            self.config = config
            self.session = aiohttp.ClientSession()
            self.max_queue_size = config.get('max_queue_size', 1000)
            return True
        except Exception as e:
            print(f"Error initializing notifications: {e}")
            return False
            
    async def send_notification(self, message: str, level: str = 'info',
                              metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Відправка сповіщення"""
        try:
            # Формуємо сповіщення
            notification = {
                'message': message,
                'level': level,
                'timestamp': datetime.now().isoformat(),
                'metadata': metadata or {}
            }
            
            # Додаємо в чергу
            self._add_to_queue(notification)
            
            # Відправляємо через Telegram
            return await self._send_telegram_notification(notification)
            
        except Exception as e:
            print(f"Error sending notification: {e}")
            return False
            
    async def send_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> bool:
        """Відправка сповіщення про помилку"""
        try:
            # Формуємо повідомлення про помилку
            error_message = (
                f"🚨 ERROR: {type(error).__name__}\n"
                f"Message: {str(error)}\n"
            )
            
            if context:
                error_message += "\nContext:\n" + "\n".join(
                    f"- {k}: {v}" for k, v in context.items()
                )
                
            # Відправляємо сповіщення
            return await self.send_notification(
                message=error_message,
                level='error',
                metadata={'error_type': type(error).__name__, 'context': context}
            )
            
        except Exception as e:
            print(f"Error sending error notification: {e}")
            return False
            
    async def send_trade_notification(self, trade_data: Dict[str, Any]) -> bool:
        """Відправка сповіщення про торгову операцію"""
        try:
            # Формуємо повідомлення про торгівлю
            trade_message = (
                f"💰 TRADE: {trade_data['operation_type']}\n"
                f"Token: {trade_data['token_address']}\n"
                f"Amount: {trade_data['amount']}\n"
                f"Price: {trade_data['price']}\n"
                f"Status: {trade_data['status']}"
            )
            
            if trade_data.get('error_message'):
                trade_message += f"\nError: {trade_data['error_message']}"
                
            # Відправляємо сповіщення
            return await self.send_notification(
                message=trade_message,
                level='info' if trade_data['status'] == 'completed' else 'warning',
                metadata=trade_data
            )
            
        except Exception as e:
            print(f"Error sending trade notification: {e}")
            return False
            
    async def send_system_notification(self, metrics: Dict[str, Any]) -> bool:
        """Відправка сповіщення про стан системи"""
        try:
            # Формуємо повідомлення про стан системи
            system_message = (
                f"📊 SYSTEM STATUS\n"
                f"CPU: {metrics['cpu']['total_percent']}%\n"
                f"Memory: {metrics['memory']['percent']}%\n"
                f"Disk: {metrics['disk']['partitions'][0]['percent']}%\n"
            )
            
            # Додаємо попередження якщо є проблеми
            alerts = []
            if metrics['cpu']['total_percent'] > 80:
                alerts.append("High CPU usage!")
            if metrics['memory']['percent'] > 80:
                alerts.append("High memory usage!")
            if metrics['disk']['partitions'][0]['percent'] > 80:
                alerts.append("Low disk space!")
                
            if alerts:
                system_message += "\n⚠️ Alerts:\n" + "\n".join(f"- {alert}" for alert in alerts)
                
            # Відправляємо сповіщення
            return await self.send_notification(
                message=system_message,
                level='warning' if alerts else 'info',
                metadata=metrics
            )
            
        except Exception as e:
            print(f"Error sending system notification: {e}")
            return False
            
    async def get_notification_history(self, level: Optional[str] = None,
                                     limit: int = 100) -> List[Dict[str, Any]]:
        """Отримання історії сповіщень"""
        try:
            if level:
                return [
                    notification for notification in self.notification_queue
                    if notification['level'] == level
                ][-limit:]
            return self.notification_queue[-limit:]
            
        except Exception as e:
            print(f"Error getting notification history: {e}")
            return []
            
    def _add_to_queue(self, notification: Dict[str, Any]) -> None:
        """Додавання сповіщення в чергу"""
        self.notification_queue.append(notification)
        if len(self.notification_queue) > self.max_queue_size:
            self.notification_queue = self.notification_queue[-self.max_queue_size:]
            
    async def _send_telegram_notification(self, notification: Dict[str, Any]) -> bool:
        """Відправка сповіщення через Telegram"""
        try:
            if not self.session:
                return False
                
            # Отримуємо токен і чат ID з конфігурації
            token = self.config.get('telegram_token')
            chat_id = self.config.get('telegram_chat_id')
            
            if not token or not chat_id:
                return False
                
            # Форматуємо повідомлення
            level_emoji = {
                'info': 'ℹ️',
                'warning': '⚠️',
                'error': '🚨'
            }
            
            formatted_message = (
                f"{level_emoji.get(notification['level'], '📝')} "
                f"{notification['message']}"
            )
            
            # Відправляємо запит до Telegram API
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            async with self.session.post(url, json={
                'chat_id': chat_id,
                'text': formatted_message,
                'parse_mode': 'HTML'
            }) as response:
                return response.status == 200
                
        except Exception as e:
            print(f"Error sending Telegram notification: {e}")
            return False
            
    async def cleanup(self) -> None:
        """Очищення ресурсів"""
        if self.session:
            await self.session.close() 