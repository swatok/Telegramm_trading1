"""Модуль для обробки помилок бази даних"""

import time
import traceback
from functools import wraps
from typing import Any, Callable, Optional, Dict, Type, Union
from datetime import datetime

from loguru import logger
import psycopg2
from psycopg2 import OperationalError, InterfaceError

from core.error_handler import BaseErrorHandler
from core.notification_manager import NotificationManager

class DatabaseError(Exception):
    """Базовий клас для помилок бази даних"""
    pass

class ConnectionError(DatabaseError):
    """Помилка підключення до бази даних"""
    pass

class QueryError(DatabaseError):
    """Помилка виконання запиту"""
    pass

class RetryStrategy:
    """Клас для налаштування стратегії повторних спроб"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 0.1,
        max_delay: float = 2.0,
        exponential_base: float = 2.0
    ):
        """
        Ініціалізація стратегії
        
        Args:
            max_attempts: Максимальна кількість спроб
            initial_delay: Початкова затримка між спробами
            max_delay: Максимальна затримка між спробами
            exponential_base: База для експоненціального відступу
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        
    def get_delay(self, attempt: int) -> float:
        """
        Розрахунок затримки для поточної спроби
        
        Args:
            attempt: Номер поточної спроби
            
        Returns:
            Час затримки в секундах
        """
        delay = min(
            self.initial_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        return delay

class DatabaseErrorHandler(BaseErrorHandler):
    """Клас для обробки помилок бази даних"""
    
    def __init__(
        self,
        postgres_connection,
        notification_manager: NotificationManager
    ):
        """
        Ініціалізація обробника помилок
        
        Args:
            postgres_connection: Об'єкт підключення до PostgreSQL
            notification_manager: Менеджер сповіщень
        """
        super().__init__(notification_manager)
        self.postgres = postgres_connection
        self.default_strategy = RetryStrategy()
        
    def with_retry(
        self,
        retry_strategy: Optional[RetryStrategy] = None,
        exceptions: tuple = (OperationalError, InterfaceError)
    ):
        """
        Декоратор для повторних спроб виконання операції
        
        Args:
            retry_strategy: Стратегія повторних спроб
            exceptions: Кортеж винятків для обробки
        """
        strategy = retry_strategy or self.default_strategy
        
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs) -> Any:
                last_exception = None
                
                for attempt in range(strategy.max_attempts):
                    try:
                        return await func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        if attempt < strategy.max_attempts - 1:
                            delay = strategy.get_delay(attempt)
                            context = {
                                "attempt": attempt + 1,
                                "max_attempts": strategy.max_attempts,
                                "delay": delay,
                                "function": func.__name__
                            }
                            await self.handle_warning(
                                f"Спроба {attempt + 1} не вдалася. "
                                f"Очікування {delay:.2f} секунд...",
                                context
                            )
                            time.sleep(delay)
                            
                            # Спроба відновити підключення
                            if isinstance(e, (OperationalError, InterfaceError)):
                                try:
                                    self.postgres.connect()
                                except Exception as conn_error:
                                    await self.handle_error(
                                        "Помилка відновлення підключення",
                                        conn_error,
                                        critical=True
                                    )
                                    
                await self.handle_error(
                    "Вичерпано всі спроби виконання операції",
                    last_exception,
                    critical=True,
                    context={"function": func.__name__}
                )
                raise last_exception
                
            return wrapper
        return decorator
        
    async def handle_connection_error(self, error: Exception) -> None:
        """
        Обробка помилки підключення
        
        Args:
            error: Об'єкт помилки
        """
        await self.handle_error(
            "Помилка підключення до бази даних",
            error,
            critical=True
        )
        
        try:
            self.postgres.disconnect()
            time.sleep(1)
            self.postgres.connect()
            logger.info("Підключення відновлено")
        except Exception as e:
            await self.handle_error(
                "Не вдалося відновити підключення",
                e,
                critical=True
            )
            raise ConnectionError("Не вдалося відновити підключення до бази даних")
            
    async def handle_query_error(
        self,
        error: Exception,
        query: str,
        params: Optional[tuple] = None
    ) -> None:
        """
        Обробка помилки запиту
        
        Args:
            error: Об'єкт помилки
            query: SQL запит
            params: Параметри запиту
        """
        context = {
            "query": query,
            "params": params
        }
        
        if isinstance(error, psycopg2.Error):
            context.update({
                "pg_code": error.pgcode,
                "pg_error": error.pgerror
            })
            
        await self.handle_error(
            "Помилка виконання запиту",
            error,
            context=context
        )
        
        raise QueryError(f"Помилка виконання запиту: {str(error)}")
        
    def is_connection_alive(self) -> bool:
        """
        Перевірка активності підключення
        
        Returns:
            True якщо підключення активне
        """
        try:
            return self.postgres.check_connection()
        except Exception:
            return False 