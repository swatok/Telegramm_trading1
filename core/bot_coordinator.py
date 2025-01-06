"""Модуль координації роботи бота"""

from typing import Optional
from loguru import logger

from .config_manager import ConfigManager
from .command_handler import CommandHandler
from .signal_processor import SignalProcessor
from .stats_updater import StatsUpdater
from database.repository_factory import RepositoryFactory

class BotCoordinator:
    """Клас для координації роботи всіх компонентів бота"""
    
    def __init__(self, config_path: str = '.env'):
        """
        Ініціалізація координатора
        
        Args:
            config_path: Шлях до файлу конфігурації
        """
        # Ініціалізуємо конфігурацію
        self.config = ConfigManager(config_path)
        
        # Ініціалізуємо репозиторії
        self.repository_factory = RepositoryFactory(
            db_file=self.config.get('DB_FILE', 'trading_bot.db')
        )
        
        # Ініціалізуємо обробники
        self.command_handler = CommandHandler(
            self.config,
            self.repository_factory
        )
        
        self.signal_processor = SignalProcessor(
            self.config,
            self.repository_factory
        )
        
        # Ініціалізуємо оновлювач статистики
        self.stats_updater = StatsUpdater(
            db_file=self.config.get('DB_FILE', 'trading_bot.db')
        )
        
        self._is_running = False
        
    def start(self):
        """Запуск роботи бота"""
        try:
            if self._is_running:
                logger.warning("Бот вже запущено")
                return
                
            logger.info("Запуск бота...")
            
            # Запускаємо оновлення статистики
            self.stats_updater.start()
            
            # Запускаємо обробники
            self.command_handler.start()
            self.signal_processor.start()
            
            self._is_running = True
            logger.info("Бот успішно запущено")
            
        except Exception as e:
            logger.error(f"Помилка запуску бота: {e}")
            self.stop()
            raise
            
    def stop(self):
        """Зупинка роботи бота"""
        try:
            if not self._is_running:
                logger.warning("Бот вже зупинено")
                return
                
            logger.info("Зупинка бота...")
            
            # Зупиняємо обробники
            self.command_handler.stop()
            self.signal_processor.stop()
            
            # Зупиняємо оновлення статистики
            self.stats_updater.stop()
            
            # Закриваємо з'єднання з БД
            self.repository_factory.close_all()
            
            self._is_running = False
            logger.info("Бот успішно зупинено")
            
        except Exception as e:
            logger.error(f"Помилка зупинки бота: {e}")
            raise
            
    def force_stats_update(self, days: int = 30):
        """
        Примусове оновлення статистики
        
        Args:
            days: Кількість днів для оновлення
        """
        try:
            self.stats_updater.force_update(days)
        except Exception as e:
            logger.error(f"Помилка примусового оновлення статистики: {e}")
            raise
            
    @property
    def is_running(self) -> bool:
        """
        Перевірка чи бот запущено
        
        Returns:
            True якщо бот запущено
        """
        return self._is_running
