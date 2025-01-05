"""Скрипт для перевірки роботи компонентів бази даних"""

import os
import time
from loguru import logger
from postgres_connection import PostgresConnection
from performance_monitor import PerformanceMonitor
from error_handler import ErrorHandler, RetryStrategy

def check_performance_monitor():
    """Перевірка монітора продуктивності"""
    logger.info("Перевірка Performance Monitor...")
    
    postgres = PostgresConnection()
    monitor = PerformanceMonitor(postgres)
    
    # Перевірка системних метрик
    metrics = monitor.get_system_metrics()
    logger.info(f"Системні метрики: {metrics}")
    
    # Перевірка метрик підключень
    monitor.update_connection_metrics()
    logger.info("Метрики підключень оновлено")
    
    # Перевірка метрик партицій
    monitor.update_partition_metrics()
    logger.info("Метрики партицій оновлено")
    
def check_error_handler():
    """Перевірка обробника помилок"""
    logger.info("Перевірка Error Handler...")
    
    postgres = PostgresConnection()
    handler = ErrorHandler(postgres)
    
    # Перевірка стратегії повторних спроб
    strategy = RetryStrategy(max_attempts=3, initial_delay=0.1)
    
    @handler.with_retry(retry_strategy=strategy)
    def test_query():
        return postgres.execute_query("SELECT 1", fetch=True)
    
    result = test_query()
    logger.info(f"Результат тестового запиту: {result}")
    
    # Перевірка обробки помилок підключення
    try:
        handler.handle_connection_error(Exception("Тестова помилка"))
    except Exception as e:
        logger.info(f"Очікувана помилка: {e}")

def main():
    """Головна функція"""
    logger.info("Початок перевірки компонентів...")
    
    try:
        check_performance_monitor()
        check_error_handler()
        logger.info("Всі перевірки завершено успішно")
        
    except Exception as e:
        logger.error(f"Помилка під час перевірки: {e}")
        
if __name__ == "__main__":
    main() 