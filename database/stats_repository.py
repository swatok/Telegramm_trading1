"""Репозиторій для роботи зі статистикою"""

from typing import Dict, Optional
from functools import lru_cache
from loguru import logger
from .base_repository import BaseRepository

class StatsRepository(BaseRepository):
    """Клас для роботи зі статистикою в БД"""
    
    def _create_tables(self) -> None:
        """Створення таблиць для статистики"""
        self.execute_query('''
            CREATE TABLE IF NOT EXISTS channel_stats (
                id SERIAL PRIMARY KEY,
                channel_id INTEGER REFERENCES channels(id),
                total_positions INTEGER DEFAULT 0,
                open_positions INTEGER DEFAULT 0,
                closed_positions INTEGER DEFAULT 0,
                profitable_trades INTEGER DEFAULT 0,
                losing_trades INTEGER DEFAULT 0,
                total_profit DECIMAL(20, 8) DEFAULT 0,
                win_rate DECIMAL(5, 2) DEFAULT 0,
                avg_profit DECIMAL(20, 8) DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Створюємо індекси
        self.execute_query('''
            CREATE INDEX IF NOT EXISTS idx_channel_stats_channel_id 
            ON channel_stats(channel_id)
        ''')
        
    def _clear_cache(self) -> None:
        """Очищення кешу"""
        self.get_channel_stats.cache_clear()
        self.get_all_stats.cache_clear()
        
    def update_channel_stats(self, channel_id: int) -> Optional[Dict]:
        """
        Оновлення статистики каналу
        
        Args:
            channel_id: ID каналу
            
        Returns:
            Словник з оновленими даними або None
        """
        try:
            # Отримуємо актуальну статистику з таблиці positions
            stats = self.execute_query('''
                WITH position_stats AS (
                    SELECT
                        COUNT(*) as total_positions,
                        COUNT(*) FILTER (WHERE status = 'open') as open_positions,
                        COUNT(*) FILTER (WHERE status = 'closed') as closed_positions,
                        COUNT(*) FILTER (WHERE status = 'closed' AND profit_loss > 0) as profitable_trades,
                        COUNT(*) FILTER (WHERE status = 'closed' AND profit_loss < 0) as losing_trades,
                        SUM(profit_loss) FILTER (WHERE status = 'closed') as total_profit,
                        AVG(profit_loss) FILTER (WHERE status = 'closed') as avg_profit
                    FROM positions
                    WHERE channel_id = %s
                )
                SELECT
                    total_positions,
                    open_positions,
                    closed_positions,
                    profitable_trades,
                    losing_trades,
                    COALESCE(total_profit, 0) as total_profit,
                    CASE 
                        WHEN closed_positions > 0 
                        THEN (profitable_trades::float / closed_positions * 100)
                        ELSE 0 
                    END as win_rate,
                    COALESCE(avg_profit, 0) as avg_profit
                FROM position_stats
            ''', (channel_id,), fetch=True)
            
            if not stats:
                return None
                
            # Оновлюємо статистику в таблиці channel_stats
            result = self.execute_query('''
                INSERT INTO channel_stats (
                    channel_id, total_positions, open_positions,
                    closed_positions, profitable_trades, losing_trades,
                    total_profit, win_rate, avg_profit
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (channel_id) DO UPDATE
                SET
                    total_positions = EXCLUDED.total_positions,
                    open_positions = EXCLUDED.open_positions,
                    closed_positions = EXCLUDED.closed_positions,
                    profitable_trades = EXCLUDED.profitable_trades,
                    losing_trades = EXCLUDED.losing_trades,
                    total_profit = EXCLUDED.total_profit,
                    win_rate = EXCLUDED.win_rate,
                    avg_profit = EXCLUDED.avg_profit,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING *
            ''', (
                channel_id,
                stats[0]['total_positions'],
                stats[0]['open_positions'],
                stats[0]['closed_positions'],
                stats[0]['profitable_trades'],
                stats[0]['losing_trades'],
                stats[0]['total_profit'],
                stats[0]['win_rate'],
                stats[0]['avg_profit']
            ), fetch=True)
            
            if result:
                self._clear_cache()
                return result[0]
                
            return None
            
        except Exception as e:
            logger.error(f"Помилка оновлення статистики каналу: {e}")
            return None
            
    @lru_cache(maxsize=100)
    def get_channel_stats(self, channel_id: int) -> Optional[Dict]:
        """
        Отримання статистики каналу
        
        Args:
            channel_id: ID каналу
            
        Returns:
            Словник зі статистикою або None
        """
        result = self.execute_query(
            "SELECT * FROM channel_stats WHERE channel_id = %s",
            (channel_id,),
            fetch=True
        )
        return result[0] if result else None
        
    @lru_cache(maxsize=1)
    def get_all_stats(self) -> Dict:
        """
        Отримання загальної статистики
        
        Returns:
            Словник із загальною статистикою
        """
        result = self.execute_query('''
            SELECT
                COUNT(DISTINCT channel_id) as total_channels,
                SUM(total_positions) as total_positions,
                SUM(open_positions) as open_positions,
                SUM(closed_positions) as closed_positions,
                SUM(profitable_trades) as profitable_trades,
                SUM(losing_trades) as losing_trades,
                SUM(total_profit) as total_profit,
                AVG(win_rate) as avg_win_rate,
                AVG(avg_profit) as avg_profit
            FROM channel_stats
        ''', fetch=True)
        
        return result[0] if result else {
            'total_channels': 0,
            'total_positions': 0,
            'open_positions': 0,
            'closed_positions': 0,
            'profitable_trades': 0,
            'losing_trades': 0,
            'total_profit': 0,
            'avg_win_rate': 0,
            'avg_profit': 0
        }
