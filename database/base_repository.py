"""Базовий клас для репозиторіїв"""

from typing import List, Dict, Optional, Any, Tuple, Union
from loguru import logger
from .postgres_connection import PostgresConnection

class BaseRepository:
    """Базовий клас для всіх репозиторіїв"""
    
    def __init__(self):
        """Ініціалізація базового репозиторію"""
        self.connection = PostgresConnection()
        self._create_tables()
        
    def _create_tables(self) -> None:
        """
        Створення необхідних таблиць
        Має бути перевизначено в дочірніх класах
        """
        raise NotImplementedError
        
    def execute_query(
        self,
        query: str,
        params: Optional[Union[Tuple, List, Dict]] = None,
        fetch: bool = False
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Виконання SQL запиту
        
        Args:
            query: SQL запит
            params: Параметри запиту
            fetch: Чи потрібно повертати результат
            
        Returns:
            Список словників з результатами або None
        """
        try:
            with self.connection as conn:
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                
                if fetch:
                    columns = [desc[0] for desc in cursor.description]
                    results = []
                    
                    for row in cursor.fetchall():
                        results.append(dict(zip(columns, row)))
                        
                    return results
                    
                return None
                
        except Exception as e:
            logger.error(f"Помилка виконання запиту: {e}")
            logger.error(f"Запит: {query}")
            logger.error(f"Параметри: {params}")
            raise 