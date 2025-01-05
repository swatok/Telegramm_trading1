"""Репозиторій для роботи з торгами"""

from typing import List, Dict, Optional
from functools import lru_cache
from loguru import logger
from .base_repository import BaseRepository

class TradeRepository(BaseRepository):
    """Клас для роботи з торгами в БД"""
    
    def _create_tables(self) -> None:
        """Створення таблиць для торгів"""
        self.execute_query('''
            CREATE TABLE IF NOT EXISTS trades (
                id SERIAL PRIMARY KEY,
                position_id INTEGER REFERENCES positions(id),
                pair VARCHAR(20) NOT NULL,
                entry_price DECIMAL(20, 8) NOT NULL,
                exit_price DECIMAL(20, 8),
                quantity DECIMAL(20, 8) NOT NULL,
                trade_type VARCHAR(10) NOT NULL,
                status VARCHAR(20) DEFAULT 'open',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closed_at TIMESTAMP,
                profit_loss DECIMAL(20, 8)
            )
        ''')
        
        # Створюємо індекси
        self.execute_query('''
            CREATE INDEX IF NOT EXISTS idx_trades_position_id 
            ON trades(position_id)
        ''')
        
        self.execute_query('''
            CREATE INDEX IF NOT EXISTS idx_trades_pair 
            ON trades(pair)
        ''')
        
        self.execute_query('''
            CREATE INDEX IF NOT EXISTS idx_trades_status 
            ON trades(status)
        ''')
        
    def _clear_cache(self) -> None:
        """Очищення кешу"""
        self.get_trade.cache_clear()
        self.get_position_trades.cache_clear()
        self.get_open_trades.cache_clear()
        self.get_closed_trades.cache_clear()
        
    def add_trade(
        self,
        position_id: int,
        pair: str,
        entry_price: float,
        quantity: float,
        trade_type: str = 'long'
    ) -> Optional[Dict]:
        """
        Додавання нового торгу
        
        Args:
            position_id: ID позиції
            pair: Торгова пара
            entry_price: Ціна входу
            quantity: Кількість
            trade_type: Тип торгу (long/short)
            
        Returns:
            Словник з даними торгу або None
        """
        try:
            result = self.execute_query('''
                INSERT INTO trades (
                    position_id, pair, entry_price,
                    quantity, trade_type
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING *
            ''', (
                position_id, pair, entry_price,
                quantity, trade_type
            ), fetch=True)
            
            if result:
                self._clear_cache()
                return result[0]
                
            return None
            
        except Exception as e:
            logger.error(f"Помилка додавання торгу: {e}")
            return None
            
    def close_trade(
        self,
        trade_id: int,
        exit_price: float
    ) -> Optional[Dict]:
        """
        Закриття торгу
        
        Args:
            trade_id: ID торгу
            exit_price: Ціна виходу
            
        Returns:
            Словник з оновленими даними або None
        """
        try:
            # Отримуємо дані торгу
            trade = self.get_trade(trade_id)
            if not trade or trade['status'] != 'open':
                return None
                
            # Розраховуємо прибуток/збиток
            entry_price = float(trade['entry_price'])
            quantity = float(trade['quantity'])
            
            profit_loss = (
                (exit_price - entry_price) * quantity
                if trade['trade_type'] == 'long'
                else (entry_price - exit_price) * quantity
            )
            
            # Оновлюємо торг
            result = self.execute_query('''
                UPDATE trades
                SET status = 'closed',
                    exit_price = %s,
                    profit_loss = %s,
                    closed_at = CURRENT_TIMESTAMP
                WHERE id = %s AND status = 'open'
                RETURNING *
            ''', (exit_price, profit_loss, trade_id), fetch=True)
            
            if result:
                self._clear_cache()
                return result[0]
                
            return None
            
        except Exception as e:
            logger.error(f"Помилка закриття торгу: {e}")
            return None
            
    @lru_cache(maxsize=100)
    def get_trade(self, trade_id: int) -> Optional[Dict]:
        """
        Отримання торгу за ID
        
        Args:
            trade_id: ID торгу
            
        Returns:
            Словник з даними торгу або None
        """
        result = self.execute_query(
            "SELECT * FROM trades WHERE id = %s",
            (trade_id,),
            fetch=True
        )
        return result[0] if result else None
        
    @lru_cache(maxsize=50)
    def get_position_trades(
        self,
        position_id: int,
        limit: int = 100
    ) -> List[Dict]:
        """
        Отримання торгів позиції
        
        Args:
            position_id: ID позиції
            limit: Ліміт кількості записів
            
        Returns:
            Список словників з даними торгів
        """
        return self.execute_query('''
            SELECT * FROM trades 
            WHERE position_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        ''', (position_id, limit), fetch=True) or []
        
    @lru_cache(maxsize=1)
    def get_open_trades(self) -> List[Dict]:
        """
        Отримання відкритих торгів
        
        Returns:
            Список словників з даними торгів
        """
        return self.execute_query(
            "SELECT * FROM trades WHERE status = 'open'",
            fetch=True
        ) or []
        
    @lru_cache(maxsize=1)
    def get_closed_trades(
        self,
        limit: int = 100
    ) -> List[Dict]:
        """
        Отримання закритих торгів
        
        Args:
            limit: Ліміт кількості записів
            
        Returns:
            Список словників з даними торгів
        """
        return self.execute_query('''
            SELECT * FROM trades 
            WHERE status = 'closed'
            ORDER BY closed_at DESC
            LIMIT %s
        ''', (limit,), fetch=True) or [] 