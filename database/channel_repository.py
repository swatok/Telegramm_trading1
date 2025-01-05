"""Репозиторій для роботи з каналами"""

from typing import List, Dict, Optional
from functools import lru_cache
from loguru import logger
from .base_repository import BaseRepository

class ChannelRepository(BaseRepository):
    """Клас для роботи з каналами в БД"""
    
    def _create_tables(self) -> None:
        """Створення таблиць для каналів"""
        self.execute_query('''
            CREATE TABLE IF NOT EXISTS channels (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                username VARCHAR(255) NOT NULL,
                title VARCHAR(255) NOT NULL,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Створюємо індекси
        self.execute_query('''
            CREATE INDEX IF NOT EXISTS idx_channels_telegram_id 
            ON channels(telegram_id)
        ''')
        
        self.execute_query('''
            CREATE INDEX IF NOT EXISTS idx_channels_username 
            ON channels(username)
        ''')
        
    def _clear_cache(self) -> None:
        """Очищення кешу"""
        self.get_channel.cache_clear()
        self.get_channel_by_telegram_id.cache_clear()
        self.get_channel_by_username.cache_clear()
        self.get_active_channels.cache_clear()
        self.get_all_channels.cache_clear()
        
    def add_channel(
        self,
        telegram_id: int,
        username: str,
        title: str
    ) -> Optional[Dict]:
        """
        Додавання нового каналу
        
        Args:
            telegram_id: Telegram ID каналу
            username: Ім'я користувача каналу
            title: Назва каналу
            
        Returns:
            Словник з даними каналу або None
        """
        try:
            result = self.execute_query('''
                INSERT INTO channels (telegram_id, username, title)
                VALUES (%s, %s, %s)
                RETURNING *
            ''', (telegram_id, username, title), fetch=True)
            
            if result:
                self._clear_cache()
                return result[0]
                
            return None
            
        except Exception as e:
            logger.error(f"Помилка додавання каналу: {e}")
            return None
            
    def update_channel(
        self,
        telegram_id: int,
        username: str = None,
        title: str = None,
        is_active: bool = None
    ) -> Optional[Dict]:
        """
        Оновлення даних каналу
        
        Args:
            telegram_id: Telegram ID каналу
            username: Нове ім'я користувача
            title: Нова назва
            is_active: Новий статус активності
            
        Returns:
            Словник з оновленими даними або None
        """
        try:
            update_fields = []
            values = []
            
            if username is not None:
                update_fields.append("username = %s")
                values.append(username)
                
            if title is not None:
                update_fields.append("title = %s")
                values.append(title)
                
            if is_active is not None:
                update_fields.append("is_active = %s")
                values.append(is_active)
                
            if not update_fields:
                return None
                
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            values.append(telegram_id)
            
            query = f'''
                UPDATE channels
                SET {', '.join(update_fields)}
                WHERE telegram_id = %s
                RETURNING *
            '''
            
            result = self.execute_query(query, tuple(values), fetch=True)
            
            if result:
                self._clear_cache()
                return result[0]
                
            return None
            
        except Exception as e:
            logger.error(f"Помилка оновлення каналу: {e}")
            return None
            
    @lru_cache(maxsize=100)
    def get_channel(self, channel_id: int) -> Optional[Dict]:
        """
        Отримання каналу за ID
        
        Args:
            channel_id: ID каналу
            
        Returns:
            Словник з даними каналу або None
        """
        result = self.execute_query(
            "SELECT * FROM channels WHERE id = %s",
            (channel_id,),
            fetch=True
        )
        return result[0] if result else None
        
    @lru_cache(maxsize=100)
    def get_channel_by_telegram_id(self, telegram_id: int) -> Optional[Dict]:
        """
        Отримання каналу за Telegram ID
        
        Args:
            telegram_id: Telegram ID каналу
            
        Returns:
            Словник з даними каналу або None
        """
        result = self.execute_query(
            "SELECT * FROM channels WHERE telegram_id = %s",
            (telegram_id,),
            fetch=True
        )
        return result[0] if result else None
        
    @lru_cache(maxsize=100)
    def get_channel_by_username(self, username: str) -> Optional[Dict]:
        """
        Отримання каналу за іменем користувача
        
        Args:
            username: Ім'я користувача каналу
            
        Returns:
            Словник з даними каналу або None
        """
        result = self.execute_query(
            "SELECT * FROM channels WHERE username = %s",
            (username,),
            fetch=True
        )
        return result[0] if result else None
        
    @lru_cache(maxsize=1)
    def get_active_channels(self) -> List[Dict]:
        """
        Отримання всіх активних каналів
        
        Returns:
            Список словників з даними каналів
        """
        return self.execute_query(
            "SELECT * FROM channels WHERE is_active = true",
            fetch=True
        ) or []
        
    @lru_cache(maxsize=1)
    def get_all_channels(self) -> List[Dict]:
        """
        Отримання всіх каналів
        
        Returns:
            Список словників з даними каналів
        """
        return self.execute_query(
            "SELECT * FROM channels ORDER BY created_at DESC",
            fetch=True
        ) or [] 