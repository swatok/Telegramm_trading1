"""
Менеджер аналітики торгових операцій
"""

import asyncio
from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger

from database import (
    PositionRepository,
    TradeRepository,
    TransactionRepository
)

class TradeAnalyticsManager:
    """Менеджер аналітики торгових операцій"""
    
    def __init__(
        self,
        position_repo: PositionRepository,
        trade_repo: TradeRepository,
        transaction_repo: TransactionRepository
    ):
        self.position_repo = position_repo
        self.trade_repo = trade_repo
        self.transaction_repo = transaction_repo
        
        self._price_history: Dict[str, List[Dict]] = {}  # token_address -> [{timestamp, price}]
        self._performance_metrics: Dict = {}
        self._is_running = False
        
    async def initialize(self) -> bool:
        """Ініціалізація аналітики"""
        try:
            # Завантажуємо історичні дані
            await self._load_historical_data()
            # Ініціалізуємо метрики
            await self._initialize_metrics()
            return True
        except Exception as e:
            logger.error(f"Помилка ініціалізації аналітики: {e}")
            return False
            
    async def stop(self) -> bool:
        """Зупинка аналітики"""
        try:
            self._is_running = False
            # Зберігаємо фінальні метрики
            await self._save_metrics()
            return True
        except Exception as e:
            logger.error(f"Помилка зупинки аналітики: {e}")
            return False
            
    async def update_price_analytics(self, price_update: Dict):
        """Оновлення цінової аналітики"""
        try:
            token_address = price_update['token_address']
            price = Decimal(price_update['price'])
            timestamp = datetime.now()
            
            # Оновлюємо історію цін
            if token_address not in self._price_history:
                self._price_history[token_address] = []
            
            self._price_history[token_address].append({
                'timestamp': timestamp,
                'price': price
            })
            
            # Очищуємо старі дані (зберігаємо тільки останні 24 години)
            cutoff_time = timestamp - timedelta(hours=24)
            self._price_history[token_address] = [
                entry for entry in self._price_history[token_address]
                if entry['timestamp'] > cutoff_time
            ]
            
            # Оновлюємо метрики
            await self._update_metrics(token_address)
            
        except Exception as e:
            logger.error(f"Помилка оновлення цінової аналітики: {e}")
            
    async def get_token_analytics(self, token_address: str) -> Dict:
        """Отримання аналітики по токену"""
        try:
            if token_address not in self._price_history:
                return {
                    'token_address': token_address,
                    'price_data': [],
                    'metrics': {}
                }
                
            return {
                'token_address': token_address,
                'price_data': self._price_history[token_address],
                'metrics': self._get_token_metrics(token_address)
            }
            
        except Exception as e:
            logger.error(f"Помилка отримання аналітики токена: {e}")
            return {}
            
    async def get_portfolio_analytics(self) -> Dict:
        """Отримання аналітики портфеля"""
        try:
            return {
                'total_pnl': self._performance_metrics.get('total_pnl', Decimal(0)),
                'win_rate': self._performance_metrics.get('win_rate', Decimal(0)),
                'average_profit': self._performance_metrics.get('average_profit', Decimal(0)),
                'average_loss': self._performance_metrics.get('average_loss', Decimal(0)),
                'sharpe_ratio': self._performance_metrics.get('sharpe_ratio', Decimal(0))
            }
        except Exception as e:
            logger.error(f"Помилка отримання аналітики портфеля: {e}")
            return {}
            
    async def _load_historical_data(self):
        """Завантаження історичних даних"""
        try:
            # Завантажуємо історію торгів
            trades = await self.trade_repo.get_recent_trades(hours=24)
            for trade in trades:
                token_address = trade['token_address']
                if token_address not in self._price_history:
                    self._price_history[token_address] = []
                    
                self._price_history[token_address].append({
                    'timestamp': trade['timestamp'],
                    'price': trade['price']
                })
                
        except Exception as e:
            logger.error(f"Помилка завантаження історичних даних: {e}")
            
    async def _initialize_metrics(self):
        """Ініціалізація метрик"""
        try:
            # Завантажуємо всі закриті позиції
            closed_positions = await self.position_repo.get_closed_positions()
            
            # Розраховуємо базові метрики
            total_pnl = sum(position['pnl'] for position in closed_positions)
            winning_trades = sum(1 for position in closed_positions if position['pnl'] > 0)
            total_trades = len(closed_positions)
            
            self._performance_metrics = {
                'total_pnl': total_pnl,
                'win_rate': Decimal(winning_trades) / Decimal(total_trades) if total_trades > 0 else Decimal(0),
                'total_trades': total_trades,
                'winning_trades': winning_trades
            }
            
        except Exception as e:
            logger.error(f"Помилка ініціалізації метрик: {e}")
            
    async def _update_metrics(self, token_address: str):
        """Оновлення метрик для токена"""
        try:
            price_data = self._price_history[token_address]
            if len(price_data) < 2:
                return
                
            # Розраховуємо волатильність
            prices = [entry['price'] for entry in price_data]
            volatility = self._calculate_volatility(prices)
            
            # Оновлюємо метрики токена
            if token_address not in self._performance_metrics:
                self._performance_metrics[token_address] = {}
                
            self._performance_metrics[token_address].update({
                'volatility': volatility,
                'price_change_24h': (prices[-1] - prices[0]) / prices[0],
                'last_update': datetime.now()
            })
            
        except Exception as e:
            logger.error(f"Помилка оновлення метрик: {e}")
            
    def _calculate_volatility(self, prices: List[Decimal]) -> Decimal:
        """Розрахунок волатильності"""
        try:
            if len(prices) < 2:
                return Decimal(0)
                
            returns = [
                (prices[i] - prices[i-1]) / prices[i-1]
                for i in range(1, len(prices))
            ]
            
            mean_return = sum(returns) / len(returns)
            squared_diff = sum((r - mean_return) ** 2 for r in returns)
            variance = squared_diff / (len(returns) - 1)
            
            return Decimal(variance).sqrt()
            
        except Exception as e:
            logger.error(f"Помилка розрахунку волатильності: {e}")
            return Decimal(0)
            
    def _get_token_metrics(self, token_address: str) -> Dict:
        """Отримання метрик токена"""
        try:
            return self._performance_metrics.get(token_address, {})
        except Exception as e:
            logger.error(f"Помилка отримання метрик токена: {e}")
            return {}
            
    async def _save_metrics(self):
        """Збереження метрик"""
        try:
            # TODO: Додати збереження метрик в базу даних
            pass
        except Exception as e:
            logger.error(f"Помилка збереження метрик: {e}")
            
    async def check_health(self) -> Dict:
        """Перевірка стану аналітики"""
        try:
            return {
                'healthy': True,
                'details': {
                    'price_history_tokens': len(self._price_history),
                    'metrics_last_update': self._performance_metrics.get('last_update')
                }
            }
        except Exception as e:
            return {
                'healthy': False,
                'details': str(e)
            } 