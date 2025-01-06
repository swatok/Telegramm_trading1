"""Модуль для моніторингу продуктивності бази даних"""

import time
from functools import wraps
from typing import Dict, Optional, Any
from loguru import logger
import psutil
from prometheus_client import Counter, Gauge, Histogram

# Метрики Prometheus
QUERY_DURATION = Histogram(
    'postgres_query_duration_seconds',
    'Duration of PostgreSQL queries in seconds',
    ['query_type']
)

ACTIVE_CONNECTIONS = Gauge(
    'postgres_active_connections',
    'Number of active PostgreSQL connections'
)

PARTITION_SIZE = Gauge(
    'postgres_partition_size_bytes',
    'Size of PostgreSQL partitions in bytes',
    ['table_name', 'partition_name']
)

ERROR_COUNTER = Counter(
    'postgres_error_counter',
    'Number of PostgreSQL errors',
    ['error_type']
)

class PerformanceMonitor:
    """Клас для моніторингу продуктивності бази даних"""
    
    def __init__(self, postgres_connection):
        """
        Ініціалізація монітора продуктивності
        
        Args:
            postgres_connection: Об'єкт підключення до PostgreSQL
        """
        self.postgres = postgres_connection
        
    def measure_query_time(self, query_type: str = 'default'):
        """
        Декоратор для вимірювання часу виконання запиту
        
        Args:
            query_type: Тип запиту для метрики
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    QUERY_DURATION.labels(query_type=query_type).observe(duration)
                    
                    if duration > 1.0:  # Логуємо повільні запити
                        logger.warning(
                            f"Повільний запит {query_type}: {duration:.2f} секунд"
                        )
                    return result
                    
                except Exception as e:
                    ERROR_COUNTER.labels(error_type=type(e).__name__).inc()
                    raise
                    
            return wrapper
        return decorator
        
    def update_connection_metrics(self) -> None:
        """Оновлення метрик підключень"""
        try:
            result = self.postgres.execute_query(
                "SELECT count(*) as count FROM pg_stat_activity",
                fetch=True
            )
            active_connections = result[0]['count']
            ACTIVE_CONNECTIONS.set(active_connections)
            
        except Exception as e:
            logger.error(f"Помилка оновлення метрик підключень: {e}")
            ERROR_COUNTER.labels(error_type=type(e).__name__).inc()
            
    def update_partition_metrics(self) -> None:
        """Оновлення метрик розміру партицій"""
        try:
            query = """
                SELECT
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                FROM pg_tables
                WHERE tablename LIKE '%_partitioned_%'
            """
            
            results = self.postgres.execute_query(query, fetch=True)
            
            for result in results:
                PARTITION_SIZE.labels(
                    table_name=result['tablename'],
                    partition_name=result['schemaname']
                ).set(result['size_bytes'])
                
        except Exception as e:
            logger.error(f"Помилка оновлення метрик партицій: {e}")
            ERROR_COUNTER.labels(error_type=type(e).__name__).inc()
            
    def get_system_metrics(self) -> Dict[str, Any]:
        """
        Отримання системних метрик
        
        Returns:
            Словник з системними метриками
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
                'memory_available': memory.available,
                'disk_available': disk.free
            }
            
        except Exception as e:
            logger.error(f"Помилка отримання системних метрик: {e}")
            ERROR_COUNTER.labels(error_type=type(e).__name__).inc()
            return {} 