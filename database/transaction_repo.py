"""Репозиторій для роботи з транзакціями"""

from typing import List, Dict, Optional
from functools import lru_cache
from loguru import logger
from .base_repository import BaseRepository

class TransactionRepository(BaseRepository):
    """Клас для роботи з транзакціями в БД"""
    
    def _create_tables(self) -> None:
        """Створення таблиць для транзакцій"""
        self.execute_query('''
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                trade_id INTEGER REFERENCES trades(id),
                tx_hash VARCHAR(66) NOT NULL,
                tx_type VARCHAR(20) NOT NULL,
                amount DECIMAL(20, 8) NOT NULL,
                price DECIMAL(20, 8) NOT NULL,
                gas_price DECIMAL(20, 8) NOT NULL,
                gas_used DECIMAL(20, 8) NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                confirmed_at TIMESTAMP
            )
        ''')
        
        # Створюємо індекси
        self.execute_query('''
            CREATE INDEX IF NOT EXISTS idx_transactions_trade_id 
            ON transactions(trade_id)
        ''')
        
        self.execute_query('''
            CREATE INDEX IF NOT EXISTS idx_transactions_tx_hash 
            ON transactions(tx_hash)
        ''')
        
        self.execute_query('''
            CREATE INDEX IF NOT EXISTS idx_transactions_status 
            ON transactions(status)
        ''')
        
    def _clear_cache(self) -> None:
        """Очищення кешу"""
        self.get_transaction.cache_clear()
        self.get_transaction_by_hash.cache_clear()
        self.get_trade_transactions.cache_clear()
        self.get_pending_transactions.cache_clear()
        self.get_failed_transactions.cache_clear()
        
    def add_transaction(
        self,
        trade_id: int,
        tx_hash: str,
        tx_type: str,
        amount: float,
        price: float,
        gas_price: float,
        gas_used: float
    ) -> Optional[Dict]:
        """
        Додавання нової транзакції
        
        Args:
            trade_id: ID торгу
            tx_hash: Хеш транзакції
            tx_type: Тип транзакції
            amount: Кількість
            price: Ціна
            gas_price: Ціна газу
            gas_used: Використаний газ
            
        Returns:
            Словник з даними транзакції або None
        """
        try:
            result = self.execute_query('''
                INSERT INTO transactions (
                    trade_id, tx_hash, tx_type, amount,
                    price, gas_price, gas_used
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            ''', (
                trade_id, tx_hash, tx_type, amount,
                price, gas_price, gas_used
            ), fetch=True)
            
            if result:
                self._clear_cache()
                return result[0]
                
            return None
            
        except Exception as e:
            logger.error(f"Помилка додавання транзакції: {e}")
            return None
            
    def update_transaction_status(
        self,
        tx_hash: str,
        status: str
    ) -> Optional[Dict]:
        """
        Оновлення статусу транзакції
        
        Args:
            tx_hash: Хеш транзакції
            status: Новий статус
            
        Returns:
            Словник з оновленими даними або None
        """
        try:
            result = self.execute_query('''
                UPDATE transactions
                SET status = %s,
                    confirmed_at = CASE 
                        WHEN %s = 'confirmed' 
                        THEN CURRENT_TIMESTAMP 
                        ELSE confirmed_at 
                    END
                WHERE tx_hash = %s
                RETURNING *
            ''', (status, status, tx_hash), fetch=True)
            
            if result:
                self._clear_cache()
                return result[0]
                
            return None
            
        except Exception as e:
            logger.error(f"Помилка оновлення статусу транзакції: {e}")
            return None
            
    @lru_cache(maxsize=100)
    def get_transaction(self, transaction_id: int) -> Optional[Dict]:
        """
        Отримання транзакції за ID
        
        Args:
            transaction_id: ID транзакції
            
        Returns:
            Словник з даними транзакції або None
        """
        result = self.execute_query(
            "SELECT * FROM transactions WHERE id = %s",
            (transaction_id,),
            fetch=True
        )
        return result[0] if result else None
        
    @lru_cache(maxsize=100)
    def get_transaction_by_hash(self, tx_hash: str) -> Optional[Dict]:
        """
        Отримання транзакції за хешем
        
        Args:
            tx_hash: Хеш транзакції
            
        Returns:
            Словник з даними транзакції або None
        """
        result = self.execute_query(
            "SELECT * FROM transactions WHERE tx_hash = %s",
            (tx_hash,),
            fetch=True
        )
        return result[0] if result else None
        
    @lru_cache(maxsize=50)
    def get_trade_transactions(
        self,
        trade_id: int,
        limit: int = 100
    ) -> List[Dict]:
        """
        Отримання транзакцій торгу
        
        Args:
            trade_id: ID торгу
            limit: Ліміт кількості записів
            
        Returns:
            Список словників з даними транзакцій
        """
        return self.execute_query('''
            SELECT * FROM transactions 
            WHERE trade_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        ''', (trade_id, limit), fetch=True) or []
        
    @lru_cache(maxsize=1)
    def get_pending_transactions(self) -> List[Dict]:
        """
        Отримання очікуючих транзакцій
        
        Returns:
            Список словників з даними транзакцій
        """
        return self.execute_query(
            "SELECT * FROM transactions WHERE status = 'pending'",
            fetch=True
        ) or []
        
    @lru_cache(maxsize=1)
    def get_failed_transactions(
        self,
        limit: int = 100
    ) -> List[Dict]:
        """
        Отримання невдалих транзакцій
        
        Args:
            limit: Ліміт кількості записів
            
        Returns:
            Список словників з даними транзакцій
        """
        return self.execute_query('''
            SELECT * FROM transactions 
            WHERE status = 'failed'
            ORDER BY created_at DESC
            LIMIT %s
        ''', (limit,), fetch=True) or []
