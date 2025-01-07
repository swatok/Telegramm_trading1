"""Performance metrics repository"""

from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from .base_repository import BaseRepository
from models.performance import PerformanceMetrics

class PerformanceRepository(BaseRepository):
    """Репозиторій для роботи з метриками продуктивності"""
    
    async def create_tables(self) -> None:
        """Створення необхідних таблиць"""
        await self.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id SERIAL PRIMARY KEY,
                wallet_address TEXT NOT NULL,
                period_start TIMESTAMP NOT NULL,
                period_end TIMESTAMP NOT NULL,
                total_trades INTEGER NOT NULL DEFAULT 0,
                successful_trades INTEGER NOT NULL DEFAULT 0,
                failed_trades INTEGER NOT NULL DEFAULT 0,
                total_profit DECIMAL NOT NULL DEFAULT 0,
                total_loss DECIMAL NOT NULL DEFAULT 0,
                max_drawdown DECIMAL NOT NULL DEFAULT 0,
                best_trade_pnl DECIMAL NOT NULL DEFAULT 0,
                worst_trade_pnl DECIMAL NOT NULL DEFAULT 0,
                avg_trade_duration INTEGER NOT NULL DEFAULT 0
            );
            
            CREATE TABLE IF NOT EXISTS token_performance (
                id SERIAL PRIMARY KEY,
                metrics_id INTEGER REFERENCES performance_metrics(id) ON DELETE CASCADE,
                token_address TEXT NOT NULL,
                pnl DECIMAL NOT NULL DEFAULT 0,
                UNIQUE(metrics_id, token_address)
            );
        """)
    
    async def save_metrics(self, metrics: PerformanceMetrics) -> bool:
        """Збереження метрик продуктивності"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                try:
                    # Зберігаємо основні метрики
                    metrics_id = await conn.fetchval("""
                        INSERT INTO performance_metrics (
                            wallet_address, period_start, period_end,
                            total_trades, successful_trades, failed_trades,
                            total_profit, total_loss, max_drawdown,
                            best_trade_pnl, worst_trade_pnl, avg_trade_duration
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                        RETURNING id
                    """,
                    metrics.wallet_address,
                    metrics.period_start,
                    metrics.period_end,
                    metrics.total_trades,
                    metrics.successful_trades,
                    metrics.failed_trades,
                    metrics.total_profit,
                    metrics.total_loss,
                    metrics.max_drawdown,
                    metrics.best_trade_pnl,
                    metrics.worst_trade_pnl,
                    metrics.avg_trade_duration
                    )
                    
                    # Зберігаємо метрики по токенах
                    for token_address, pnl in metrics.token_performance.items():
                        await conn.execute("""
                            INSERT INTO token_performance (
                                metrics_id, token_address, pnl
                            ) VALUES ($1, $2, $3)
                        """,
                        metrics_id,
                        token_address,
                        pnl
                        )
                    
                    return True
                    
                except Exception as e:
                    print(f"Error saving performance metrics: {e}")
                    return False
    
    async def get_metrics(self, wallet_address: str, start_date: datetime) -> Optional[PerformanceMetrics]:
        """Отримання метрик за період"""
        metrics_data = await self.fetchrow("""
            SELECT * FROM performance_metrics 
            WHERE wallet_address = $1 AND period_start >= $2
            ORDER BY period_start DESC LIMIT 1
        """, wallet_address, start_date)
        
        if not metrics_data:
            return None
            
        token_data = await self.fetch("""
            SELECT token_address, pnl FROM token_performance
            WHERE metrics_id = $1
        """, metrics_data['id'])
        
        token_performance = {
            token['token_address']: token['pnl']
            for token in token_data
        }
        
        return PerformanceMetrics(
            wallet_address=metrics_data['wallet_address'],
            period_start=metrics_data['period_start'],
            period_end=metrics_data['period_end'],
            total_trades=metrics_data['total_trades'],
            successful_trades=metrics_data['successful_trades'],
            failed_trades=metrics_data['failed_trades'],
            total_profit=metrics_data['total_profit'],
            total_loss=metrics_data['total_loss'],
            max_drawdown=metrics_data['max_drawdown'],
            best_trade_pnl=metrics_data['best_trade_pnl'],
            worst_trade_pnl=metrics_data['worst_trade_pnl'],
            avg_trade_duration=metrics_data['avg_trade_duration'],
            token_performance=token_performance
        )
    
    async def get_all_metrics(self, wallet_address: str) -> List[PerformanceMetrics]:
        """Отримання всіх метрик для гаманця"""
        metrics_list = []
        metrics_data = await self.fetch("""
            SELECT * FROM performance_metrics 
            WHERE wallet_address = $1
            ORDER BY period_start DESC
        """, wallet_address)
        
        for data in metrics_data:
            token_data = await self.fetch("""
                SELECT token_address, pnl FROM token_performance
                WHERE metrics_id = $1
            """, data['id'])
            
            token_performance = {
                token['token_address']: token['pnl']
                for token in token_data
            }
            
            metrics = PerformanceMetrics(
                wallet_address=data['wallet_address'],
                period_start=data['period_start'],
                period_end=data['period_end'],
                total_trades=data['total_trades'],
                successful_trades=data['successful_trades'],
                failed_trades=data['failed_trades'],
                total_profit=data['total_profit'],
                total_loss=data['total_loss'],
                max_drawdown=data['max_drawdown'],
                best_trade_pnl=data['best_trade_pnl'],
                worst_trade_pnl=data['worst_trade_pnl'],
                avg_trade_duration=data['avg_trade_duration'],
                token_performance=token_performance
            )
            metrics_list.append(metrics)
            
        return metrics_list
    
    async def delete_metrics(self, wallet_address: str, before_date: datetime) -> bool:
        """Видалення старих метрик"""
        try:
            await self.execute("""
                DELETE FROM performance_metrics 
                WHERE wallet_address = $1 AND period_end < $2
            """, wallet_address, before_date)
            return True
        except Exception as e:
            print(f"Error deleting performance metrics: {e}")
            return False 