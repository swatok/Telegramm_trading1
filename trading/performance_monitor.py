"""
Модуль для моніторингу метрик продуктивності торгової системи.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import asyncio
from decimal import Decimal

from utils.logger import setup_logger
from .performance_metrics import PerformanceMetrics
from core.notification_manager import NotificationManager

logger = setup_logger(__name__)

class PerformanceMonitor:
    """
    Клас для моніторингу метрик продуктивності.
    Відстежує метрики та генерує сповіщення при досягненні порогових значень.
    """

    def __init__(
        self,
        metrics: PerformanceMetrics,
        notification_manager: NotificationManager,
        check_interval: int = 60
    ):
        """
        Ініціалізація монітора продуктивності.

        Args:
            metrics: Об'єкт для збору метрик
            notification_manager: Менеджер сповіщень
            check_interval: Інтервал перевірки в секундах
        """
        self.metrics = metrics
        self.notification_manager = notification_manager
        self.check_interval = check_interval
        self._monitoring_task = None
        self._is_running = False
        
        # Порогові значення для сповіщень
        self.thresholds = {
            'error_rate': 0.1,  # 10% помилок
            'api_response_time': 2.0,  # 2 секунди
            'trade_success_rate': 0.95,  # 95% успішних угод
            'consecutive_errors': 3  # 3 помилки підряд
        }
        
    async def start_monitoring(self):
        """Запуск моніторингу метрик."""
        if self._is_running:
            logger.warning("Моніторинг вже запущено")
            return
            
        self._is_running = True
        self._monitoring_task = asyncio.create_task(self._monitor_loop())
        logger.info("Запущено моніторинг продуктивності")
        
    async def stop_monitoring(self):
        """Зупинка моніторингу метрик."""
        if not self._is_running:
            return
            
        self._is_running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Зупинено моніторинг продуктивності")
        
    async def _monitor_loop(self):
        """Основний цикл моніторингу."""
        while self._is_running:
            try:
                await self._check_metrics()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Помилка в циклі моніторингу: {e}")
                await asyncio.sleep(5)  # Коротка пауза перед повторною спробою
                
    async def _check_metrics(self):
        """Перевірка метрик та генерація сповіщень."""
        # Перевірка статистики помилок
        error_stats = self.metrics.get_error_stats()
        trade_stats = self.metrics.get_trade_stats()
        api_stats = self.metrics.get_api_stats()
        
        alerts = []
        
        # Перевірка рівня помилок
        if error_stats['total_errors'] > 0:
            error_rate = error_stats['total_errors'] / trade_stats['total_trades']
            if error_rate > self.thresholds['error_rate']:
                alerts.append(
                    f"⚠️ Високий рівень помилок: {error_rate:.1%}"
                )
                
        # Перевірка часу відповіді API
        for endpoint, stats in api_stats.items():
            if stats['average_time'] > self.thresholds['api_response_time']:
                alerts.append(
                    f"⚠️ Повільні відповіді API для {endpoint}: "
                    f"{stats['average_time']:.2f}s"
                )
                
        # Перевірка успішності угод
        if trade_stats['total_trades'] > 0:
            success_rate = trade_stats['success_rate']
            if success_rate < self.thresholds['trade_success_rate']:
                alerts.append(
                    f"⚠️ Низький рівень успішних угод: {success_rate:.1%}"
                )
                
        # Перевірка послідовних помилок
        recent_errors = error_stats['recent_errors']
        if len(recent_errors) >= self.thresholds['consecutive_errors']:
            alerts.append(
                f"🔴 Виявлено {len(recent_errors)} послідовних помилок"
            )
            
        # Відправка сповіщень якщо є проблеми
        if alerts:
            message = "🔍 Звіт моніторингу:\n\n" + "\n".join(alerts)
            await self.notification_manager.send_notification(message)
            
    def update_thresholds(self, new_thresholds: Dict):
        """
        Оновлення порогових значень для сповіщень.
        
        Args:
            new_thresholds: Нові порогові значення
        """
        self.thresholds.update(new_thresholds)
        logger.info("Оновлено порогові значення моніторингу")
        
    async def generate_report(self) -> Dict:
        """
        Генерація повного звіту про продуктивність.
        
        Returns:
            Словник зі звітом
        """
        summary = self.metrics.get_performance_summary()
        hourly_stats = self.metrics.get_hourly_stats()
        
        report = {
            'summary': summary,
            'hourly_stats': hourly_stats,
            'thresholds': self.thresholds,
            'is_monitoring': self._is_running
        }
        
        return report 