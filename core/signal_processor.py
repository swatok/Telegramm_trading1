"""Процесор сигналів для обробки повідомлень з каналів"""

from typing import Optional, Dict, Any
import asyncio
from datetime import datetime
from telethon import TelegramClient, events
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest

from utils import get_logger, measure_time
from utils.decorators import log_execution
from .notification_manager import NotificationManager
from .config_manager import ConfigManager
from .repository_factory import RepositoryFactory

logger = get_logger("signal_processor")

class SignalProcessor:
    def __init__(
        self,
        notification_manager: NotificationManager,
        monitor_client: TelegramClient,
        db_file: str = 'trading_bot.db'
    ):
        """
        Ініціалізація обробника сигналів
        
        Args:
            notification_manager: Менеджер сповіщень
            monitor_client: Клієнт для моніторингу каналів
            db_file: Шлях до файлу бази даних
        """
        self.notification_manager = notification_manager
        self.monitor_client = monitor_client
        self.config = ConfigManager()
        self._shutdown_flag = False
        
        # Ініціалізуємо репозиторії
        self.repos = RepositoryFactory(db_file)
        
    @measure_time
    async def start_monitoring(self):
        """Запуск моніторингу каналів"""
        try:
            # Отримуємо список активних каналів
            channels = self.repos.channel_repository.get_active_channels()
            logger.info(f"Знайдено {len(channels)} активних каналів для моніторингу")
            
            # Підключаємося до кожного каналу
            for channel in channels:
                await self._join_channel(channel['username'])
            
            # Реєструємо обробник повідомлень
            @self.monitor_client.on(events.NewMessage)
            async def message_handler(event):
                if self._shutdown_flag:
                    return
                    
                try:
                    # Перевіряємо чи повідомлення з відстежуваного каналу
                    channel_name = event.chat.username or event.chat.title
                    channel = self.repos.channel_repository.get_channel_by_username(channel_name)
                    if not channel or not channel['is_active']:
                        return
                        
                    # Обробляємо повідомлення
                    await self._process_message(event, channel['id'])
                    
                except Exception as e:
                    logger.error(f"Помилка обробки повідомлення: {e}")
                    await self.notification_manager.send_error_notification(
                        str(e),
                        "MessageProcessingError",
                        {"channel": channel_name}
                    )
            
            logger.info("Моніторинг каналів запущено")
            
        except Exception as e:
            logger.error(f"Помилка запуску моніторингу: {e}")
            await self.notification_manager.send_error_notification(
                str(e),
                "MonitoringStartError"
            )
            raise
            
    async def stop_monitoring(self):
        """Зупинка моніторингу"""
        self._shutdown_flag = True
        self.repos.close_all()
        logger.info("Моніторинг каналів зупинено")
        
    @log_execution
    async def _join_channel(self, channel_name: str):
        """
        Приєднання до каналу
        
        Args:
            channel_name: Назва каналу
        """
        try:
            channel = await self.monitor_client.get_entity(channel_name)
            await self.monitor_client(JoinChannelRequest(channel))
            logger.info(f"Успішно приєднано до каналу {channel_name}")
            
        except Exception as e:
            logger.error(f"Помилка приєднання до каналу {channel_name}: {e}")
            await self.notification_manager.send_error_notification(
                str(e),
                "ChannelJoinError",
                {"channel": channel_name}
            )
            
    @log_execution
    async def _leave_channel(self, channel_name: str):
        """
        Вихід з каналу
        
        Args:
            channel_name: Назва каналу
        """
        try:
            channel = await self.monitor_client.get_entity(channel_name)
            await self.monitor_client(LeaveChannelRequest(channel))
            logger.info(f"Успішно покинуто канал {channel_name}")
            
        except Exception as e:
            logger.error(f"Помилка виходу з каналу {channel_name}: {e}")
            
    @measure_time
    async def _process_message(self, event, channel_id: int):
        """
        Обробка повідомлення з каналу
        
        Args:
            event: Подія нового повідомлення
            channel_id: ID каналу
        """
        try:
            # Отримуємо текст повідомлення
            message_text = event.message.text
            message_id = event.message.id
            
            # Перевіряємо чи повідомлення вже оброблено
            existing_signal = self.repos.signal_repository.get_signal(message_id, channel_id)
            if existing_signal:
                logger.debug(f"Повідомлення {message_id} вже оброблено")
                return
            
            # Парсимо повідомлення
            from message_parser import MessageParser
            signal_data = MessageParser.parse_message(message_text)
            
            if not signal_data:
                logger.debug("Повідомлення не містить торгового сигналу")
                return
                
            # Валідуємо дані сигналу
            if not self._validate_signal(signal_data):
                logger.warning("Сигнал не пройшов валідацію")
                return
                
            # Додаємо дані про канал та повідомлення
            signal_data.update({
                'message_id': message_id,
                'channel_id': channel_id,
                'status': 'received',
                'timestamp': datetime.now()
            })
            
            # Зберігаємо сигнал в базу даних
            signal_id = self.repos.signal_repository.add_signal(signal_data)
            
            # Відправляємо сповіщення про новий сигнал
            await self.notification_manager.send_notification(
                f"📊 Отримано новий сигнал\n\n"
                f"Токен: {signal_data['token_symbol']}\n"
                f"Тип: {signal_data['signal_type']}\n"
                f"Ціна: {signal_data['price']}"
            )
            
            logger.info(f"Успішно оброблено сигнал {signal_id}")
            
        except Exception as e:
            logger.error(f"Помилка обробки повідомлення: {e}")
            await self.notification_manager.send_error_notification(
                str(e),
                "SignalProcessingError"
            )
            
    def _validate_signal(self, signal_data: Dict[str, Any]) -> bool:
        """
        Валідація даних сигналу
        
        Args:
            signal_data: Дані сигналу
            
        Returns:
            bool: Результат валідації
        """
        required_fields = ['token_symbol', 'signal_type', 'price']
        
        # Перевіряємо наявність всіх обов'язкових полів
        if not all(field in signal_data for field in required_fields):
            logger.warning(f"Відсутні обов'язкові поля в сигналі: {required_fields}")
            return False
            
        # Перевіряємо тип сигналу
        if signal_data['signal_type'] not in ['BUY', 'SELL']:
            logger.warning(f"Невірний тип сигналу: {signal_data['signal_type']}")
            return False
            
        # Перевіряємо ціну
        try:
            price = float(signal_data['price'])
            if price <= 0:
                logger.warning(f"Невірна ціна в сигналі: {price}")
                return False
        except (ValueError, TypeError):
            logger.warning(f"Помилка конвертації ціни: {signal_data['price']}")
            return False
            
        return True
