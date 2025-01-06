"""Модуль для керування підключенням до PostgreSQL"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from typing import Optional, Dict, List, Any
from loguru import logger

class PostgresConnection:
    """Клас для керування підключенням до PostgreSQL"""
    
    def __init__(
        self,
        min_connections: int = 1,
        max_connections: int = 10,
        **kwargs
    ):
        """
        Ініціалізація менеджера підключень
        
        Args:
            min_connections: Мінімальна кількість підключень
            max_connections: Максимальна кількість підключень
            **kwargs: Додаткові параметри підключення
        """
        self.connection_params = {
            'dbname': os.getenv('DB_NAME', 'trading_bot'),
            'user': os.getenv('DB_USER', 'trading_user'),
            'password': os.getenv('DB_PASSWORD', 'trading_password'),
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', 5432),
            **kwargs
        }
        
        self.pool = None
        self.min_connections = min_connections
        self.max_connections = max_connections
        
    def connect(self) -> None:
        """Створення пулу підключень"""
        try:
            if self.pool is None:
                self.pool = SimpleConnectionPool(
                    minconn=self.min_connections,
                    maxconn=self.max_connections,
                    **self.connection_params
                )
                logger.info("Створено пул підключень до PostgreSQL")
                
        except Exception as e:
            logger.error(f"Помилка створення пулу підключень: {e}")
            raise
            
    def disconnect(self) -> None:
        """Закриття пулу підключень"""
        if self.pool:
            self.pool.closeall()
            self.pool = None
            logger.info("Закрито пул підключень")
            
    def get_connection(self):
        """
        Отримання підключення з пулу
        
        Returns:
            Об'єкт підключення
        """
        if self.pool is None:
            self.connect()
            
        return self.pool.getconn()
        
    def put_connection(self, conn) -> None:
        """
        Повернення підключення в пул
        
        Args:
            conn: Об'єкт підключення
        """
        if self.pool:
            self.pool.putconn(conn)
            
    def execute_query(
        self,
        query: str,
        params: tuple = None,
        fetch: bool = False,
        many: bool = False
    ) -> Optional[List[Dict]]:
        """
        Виконання SQL запиту
        
        Args:
            query: SQL запит
            params: Параметри запиту
            fetch: Чи потрібно повертати результат
            many: Чи виконувати масове вставлення
            
        Returns:
            Список словників з результатами або None
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                if many:
                    cursor.executemany(query, params or [])
                else:
                    cursor.execute(query, params or ())
                    
                if fetch:
                    result = cursor.fetchall()
                    return [dict(row) for row in result]
                    
                conn.commit()
                return None
                
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Помилка виконання запиту: {e}")
            raise
            
        finally:
            if conn:
                self.put_connection(conn)
                
    def execute_transaction(
        self,
        queries: List[tuple]
    ) -> Optional[List[Dict]]:
        """
        Виконання транзакції
        
        Args:
            queries: Список кортежів (запит, параметри, fetch)
            
        Returns:
            Список результатів або None
        """
        conn = None
        try:
            conn = self.get_connection()
            results = []
            
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                for query, params, fetch in queries:
                    cursor.execute(query, params or ())
                    
                    if fetch:
                        result = cursor.fetchall()
                        results.append([dict(row) for row in result])
                    else:
                        results.append(None)
                        
                conn.commit()
                return results if any(results) else None
                
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Помилка виконання транзакції: {e}")
            raise
            
        finally:
            if conn:
                self.put_connection(conn)
                
    def create_tables(self, queries: List[str]) -> None:
        """
        Створення таблиць
        
        Args:
            queries: Список SQL запитів
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                for query in queries:
                    cursor.execute(query)
                conn.commit()
                
            logger.info("Створено таблиці")
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Помилка створення таблиць: {e}")
            raise
            
        finally:
            if conn:
                self.put_connection(conn)
                
    def create_indexes(self, queries: List[str]) -> None:
        """
        Створення індексів
        
        Args:
            queries: Список SQL запитів
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                for query in queries:
                    cursor.execute(query)
                conn.commit()
                
            logger.info("Створено індекси")
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Помилка створення індексів: {e}")
            raise
            
        finally:
            if conn:
                self.put_connection(conn)
                
    def check_connection(self) -> bool:
        """
        Перевірка підключення
        
        Returns:
            True якщо підключення активне
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
                
        except Exception as e:
            logger.error(f"Помилка перевірки підключення: {e}")
            return False
            
        finally:
            if conn:
                self.put_connection(conn) 