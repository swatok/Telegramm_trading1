"""Репозиторій для роботи з позиціями"""

from typing import List, Dict, Optional, Any
from decimal import Decimal
from datetime import datetime
from functools import lru_cache
from loguru import logger
from .base_repository import BaseRepository

class PositionRepository(BaseRepository):
    """Клас для роботи з позиціями в БД"""
    
    def _create_tables(self) -> None:
        """Створення таблиць для позицій"""
        self.execute_query('''
            CREATE TABLE IF NOT EXISTS positions (
                id SERIAL PRIMARY KEY,
                token_address VARCHAR(64) NOT NULL,
                initial_amount DECIMAL(20, 8) NOT NULL,
                entry_price DECIMAL(20, 8) NOT NULL,
                remaining_amount DECIMAL(20, 8) NOT NULL,
                current_price DECIMAL(20, 8),
                pnl DECIMAL(20, 8),
                take_profit_levels JSONB,
                stop_loss_level DECIMAL(20, 8),
                triggered_levels JSONB,
                take_profit_hits JSONB,
                stop_loss_hit BOOLEAN DEFAULT FALSE,
                exit_history JSONB,
                is_active BOOLEAN DEFAULT TRUE,
                close_price DECIMAL(20, 8),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closed_at TIMESTAMP,
                metadata JSONB
            )
        ''')
        
        # Створюємо індекси
        self.execute_query('''
            CREATE INDEX IF NOT EXISTS idx_positions_token_address 
            ON positions(token_address)
        ''')
        
        self.execute_query('''
            CREATE INDEX IF NOT EXISTS idx_positions_is_active 
            ON positions(is_active)
        ''')
        
    def _clear_cache(self) -> None:
        """Очищення кешу"""
        self.get_position.cache_clear()
        self.get_active_positions.cache_clear()
        self.get_closed_positions.cache_clear()
        
    async def create(self, position_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Створення нової позиції
        
        Args:
            position_data: Дані позиції
            
        Returns:
            Словник з даними створеної позиції або None
        """
        try:
            columns = ', '.join(position_data.keys())
            placeholders = ', '.join(['%s'] * len(position_data))
            values = tuple(position_data.values())
            
            result = await self.execute_query(f'''
                INSERT INTO positions ({columns})
                VALUES ({placeholders})
                RETURNING *
            ''', values, fetch=True)
            
            if result:
                self._clear_cache()
                return result[0]
                
            return None
            
        except Exception as e:
            logger.error(f"Помилка створення позиції: {e}")
            return None
            
    async def update(
        self,
        token_address: str,
        position_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Оновлення позиції
        
        Args:
            token_address: Адреса токену
            position_data: Дані для оновлення
            
        Returns:
            Оновлені дані позиції або None
        """
        try:
            set_clause = ', '.join([f"{k} = %s" for k in position_data.keys()])
            values = tuple(position_data.values()) + (token_address,)
            
            result = await self.execute_query(f'''
                UPDATE positions
                SET {set_clause}
                WHERE token_address = %s
                RETURNING *
            ''', values, fetch=True)
            
            if result:
                self._clear_cache()
                return result[0]
                
            return None
            
        except Exception as e:
            logger.error(f"Помилка оновлення позиції: {e}")
            return None
            
    @lru_cache(maxsize=100)
    async def get_position(self, token_address: str) -> Optional[Dict[str, Any]]:
        """
        Отримання позиції за адресою токену
        
        Args:
            token_address: Адреса токену
            
        Returns:
            Дані позиції або None
        """
        result = await self.execute_query(
            "SELECT * FROM positions WHERE token_address = %s",
            (token_address,),
            fetch=True
        )
        return result[0] if result else None
        
    @lru_cache(maxsize=1)
    async def get_active_positions(self) -> List[Dict[str, Any]]:
        """
        Отримання активних позицій
        
        Returns:
            Список активних позицій
        """
        return await self.execute_query(
            "SELECT * FROM positions WHERE is_active = TRUE",
            fetch=True
        ) or []
        
    @lru_cache(maxsize=1)
    async def get_closed_positions(
        self,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Отримання закритих позицій
        
        Args:
            limit: Ліміт кількості записів
            
        Returns:
            Список закритих позицій
        """
        return await self.execute_query('''
            SELECT * FROM positions 
            WHERE is_active = FALSE
            ORDER BY closed_at DESC
            LIMIT %s
        ''', (limit,), fetch=True) or []
        
    async def delete(self, token_address: str) -> bool:
        """
        Видалення позиції
        
        Args:
            token_address: Адреса токену
            
        Returns:
            True якщо позиція видалена успішно
        """
        try:
            result = await self.execute_query(
                "DELETE FROM positions WHERE token_address = %s",
                (token_address,)
            )
            self._clear_cache()
            return bool(result)
            
        except Exception as e:
            logger.error(f"Помилка видалення позиції: {e}")
            return False
