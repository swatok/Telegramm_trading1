"""Модуль для оновлення статистики"""

import asyncio
from datetime import date, timedelta
from typing import Optional
from loguru import logger
from ..database.stats_repository import StatsRepository
from ..database.channel_repository import ChannelRepository
from ..database.position_repository import PositionRepository

class StatsUpdater:
    """Клас для оновлення статистики"""
    
    def __init__(
        self,
        stats_repository: StatsRepository,
        channel_repository: ChannelRepository,
        position_repository: PositionRepository,
        update_interval: int = 300  # 5 хвилин
    ):
        """
        Ініціалізація оновлювача статистики
        
        Args:
            stats_repository: Репозиторій статистики
            channel_repository: Репозиторій каналів
            position_repository: Репозиторій позицій
            update_interval: Інтервал оновлення в секундах
        """
        self.stats_repository = stats_repository
        self.channel_repository = channel_repository
        self.position_repository = position_repository
        self.update_interval = update_interval
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        
    async def start(self) -> None:
        """Запуск оновлення статистики"""
        if self.is_running:
            logger.warning("Оновлення статистики вже запущено")
            return
            
        self.is_running = True
        self._task = asyncio.create_task(self._update_loop())
        logger.info("Запущено оновлення статистики")
        
    async def stop(self) -> None:
        """Зупинка оновлення статистики"""
        if not self.is_running:
            logger.warning("Оновлення статистики не запущено")
            return
            
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
            
        logger.info("Зупинено оновлення статистики")
        
    async def _update_loop(self) -> None:
        """Цикл оновлення статистики"""
        while self.is_running:
            try:
                await self._update_stats()
                await asyncio.sleep(self.update_interval)
                
            except asyncio.CancelledError:
                break
                
            except Exception as e:
                logger.error(f"Помилка оновлення статистики: {e}")
                await asyncio.sleep(60)  # Чекаємо хвилину перед повторною спробою
                
    async def _update_stats(self) -> None:
        """Оновлення всієї статистики"""
        try:
            # Оновлюємо щоденну статистику
            today = date.today()
            self.stats_repository.update_daily_stats(today)
            
            # Оновлюємо статистику каналів
            channels = self.channel_repository.get_active_channels()
            for channel in channels:
                self.stats_repository.update_channel_stats(channel['id'], today)
                
            # Оновлюємо статистику пар
            positions = self.position_repository.get_open_positions()
            pairs = {position['pair'] for position in positions}
            for pair in pairs:
                self.stats_repository.update_pair_stats(pair, today)
                
            logger.info("Оновлено статистику")
            
        except Exception as e:
            logger.error(f"Помилка оновлення статистики: {e}")
            raise
            
    async def update_historical_stats(self, days: int = 30) -> None:
        """
        Оновлення історичної статистики
        
        Args:
            days: Кількість днів для оновлення
        """
        try:
            start_date = date.today() - timedelta(days=days)
            current_date = start_date
            
            while current_date <= date.today():
                # Оновлюємо щоденну статистику
                self.stats_repository.update_daily_stats(current_date)
                
                # Оновлюємо статистику каналів
                channels = self.channel_repository.get_active_channels()
                for channel in channels:
                    self.stats_repository.update_channel_stats(
                        channel['id'],
                        current_date
                    )
                    
                # Оновлюємо статистику пар
                positions = self.position_repository.get_open_positions()
                pairs = {position['pair'] for position in positions}
                for pair in pairs:
                    self.stats_repository.update_pair_stats(pair, current_date)
                    
                current_date += timedelta(days=1)
                
            logger.info(f"Оновлено історичну статистику за {days} днів")
            
        except Exception as e:
            logger.error(f"Помилка оновлення історичної статистики: {e}")
            raise 