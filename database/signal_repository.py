"""Репозиторій для роботи з сигналами"""

from typing import List, Dict, Optional
from functools import lru_cache
from loguru import logger
from .base_repository import BaseRepository

class SignalRepository(BaseRepository):
    """Клас для роботи з сигналами в БД"""
    
    def _create_tables(self) -> None:
        """Створення таблиць для сигналів"""
        self.execute_query('''
            CREATE TABLE IF NOT EXISTS signals (
                id SERIAL PRIMARY KEY,
                channel_id INTEGER REFERENCES channels(id),
                message_id BIGINT NOT NULL,
                pair VARCHAR(20) NOT NULL,
                entry_price DECIMAL(20, 8) NOT NULL,
                take_profit DECIMAL(20, 8),
                stop_loss DECIMAL(20, 8),
                signal_type VARCHAR(10) NOT NULL,
                status VARCHAR(20) DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                error_message TEXT
            )
        ''')
        
        # Створюємо індекси
        self.execute_query('''
            CREATE INDEX IF NOT EXISTS idx_signals_channel_id 
            ON signals(channel_id)
        ''')
        
        self.execute_query('''
            CREATE INDEX IF NOT EXISTS idx_signals_message_id 
            ON signals(message_id)
        ''')
        
        self.execute_query('''
            CREATE INDEX IF NOT EXISTS idx_signals_status 
            ON signals(status)
        ''')
        
        self.execute_query('''
            CREATE INDEX IF NOT EXISTS idx_signals_pair 
            ON signals(pair)
        ''')
        
    def _clear_cache(self) -> None:
        """Очищення кешу"""
        self.get_signal.cache_clear()
        self.get_signal_by_message.cache_clear()
        self.get_channel_signals.cache_clear()
        self.get_unprocessed_signals.cache_clear()
        self.get_failed_signals.cache_clear()
        
    def add_signal(
        self,
        channel_id: int,
        message_id: int,
        pair: str,
        entry_price: float,
        take_profit: float = None,
        stop_loss: float = None,
        signal_type: str = 'long'
    ) -> Optional[Dict]:
        """
        Додавання нового сигналу
        
        Args:
            channel_id: ID каналу
            message_id: ID повідомлення
            pair: Торгова пара
            entry_price: Ціна входу
            take_profit: Ціна take profit
            stop_loss: Ціна stop loss
            signal_type: Тип сигналу (long/short)
            
        Returns:
            Словник з даними сигналу або None
        """
        try:
            result = self.execute_query('''
                INSERT INTO signals (
                    channel_id, message_id, pair, entry_price,
                    take_profit, stop_loss, signal_type
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            ''', (
                channel_id, message_id, pair, entry_price,
                take_profit, stop_loss, signal_type
            ), fetch=True)
            
            if result:
                self._clear_cache()
                return result[0]
                
            return None
            
        except Exception as e:
            logger.error(f"Помилка додавання сигналу: {e}")
            return None
            
    def update_signal_status(
        self,
        signal_id: int,
        status: str,
        error_message: str = None
    ) -> Optional[Dict]:
        """
        Оновлення статусу сигналу
        
        Args:
            signal_id: ID сигналу
            status: Новий статус
            error_message: Повідомлення про помилку
            
        Returns:
            Словник з оновленими даними або None
        """
        try:
            result = self.execute_query('''
                UPDATE signals
                SET status = %s,
                    error_message = %s,
                    processed_at = CASE 
                        WHEN %s IN ('processed', 'failed') 
                        THEN CURRENT_TIMESTAMP 
                        ELSE processed_at 
                    END
                WHERE id = %s
                RETURNING *
            ''', (status, error_message, status, signal_id), fetch=True)
            
            if result:
                self._clear_cache()
                return result[0]
                
            return None
            
        except Exception as e:
            logger.error(f"Помилка оновлення статусу сигналу: {e}")
            return None
            
    @lru_cache(maxsize=100)
    def get_signal(self, signal_id: int) -> Optional[Dict]:
        """
        Отримання сигналу за ID
        
        Args:
            signal_id: ID сигналу
            
        Returns:
            Словник з даними сигналу або None
        """
        result = self.execute_query(
            "SELECT * FROM signals WHERE id = %s",
            (signal_id,),
            fetch=True
        )
        return result[0] if result else None
        
    @lru_cache(maxsize=100)
    def get_signal_by_message(
        self,
        channel_id: int,
        message_id: int
    ) -> Optional[Dict]:
        """
        Отримання сигналу за ID повідомлення
        
        Args:
            channel_id: ID каналу
            message_id: ID повідомлення
            
        Returns:
            Словник з даними сигналу або None
        """
        result = self.execute_query('''
            SELECT * FROM signals 
            WHERE channel_id = %s AND message_id = %s
        ''', (channel_id, message_id), fetch=True)
        return result[0] if result else None
        
    @lru_cache(maxsize=50)
    def get_channel_signals(
        self,
        channel_id: int,
        limit: int = 100
    ) -> List[Dict]:
        """
        Отримання сигналів каналу
        
        Args:
            channel_id: ID каналу
            limit: Ліміт кількості записів
            
        Returns:
            Список словників з даними сигналів
        """
        return self.execute_query('''
            SELECT * FROM signals 
            WHERE channel_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        ''', (channel_id, limit), fetch=True) or []
        
    @lru_cache(maxsize=1)
    def get_unprocessed_signals(self) -> List[Dict]:
        """
        Отримання необроблених сигналів
        
        Returns:
            Список словників з даними сигналів
        """
        return self.execute_query(
            "SELECT * FROM signals WHERE status = 'new'",
            fetch=True
        ) or []
        
    @lru_cache(maxsize=1)
    def get_failed_signals(
        self,
        limit: int = 100
    ) -> List[Dict]:
        """
        Отримання сигналів з помилками
        
        Args:
            limit: Ліміт кількості записів
            
        Returns:
            Список словників з даними сигналів
        """
        return self.execute_query('''
            SELECT * FROM signals 
            WHERE status = 'failed'
            ORDER BY processed_at DESC
            LIMIT %s
        ''', (limit,), fetch=True) or [] 