"""Performance metrics model"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Dict, List

@dataclass
class PerformanceMetrics:
    """Клас для представлення метрик продуктивності"""
    wallet_address: str
    period_start: datetime
    period_end: datetime = field(default_factory=datetime.now)
    total_trades: int = 0
    successful_trades: int = 0
    failed_trades: int = 0
    total_profit: Decimal = Decimal('0')
    total_loss: Decimal = Decimal('0')
    max_drawdown: Decimal = Decimal('0')
    best_trade_pnl: Decimal = Decimal('0')
    worst_trade_pnl: Decimal = Decimal('0')
    avg_trade_duration: int = 0  # в секундах
    token_performance: Dict[str, Decimal] = field(default_factory=dict)
    
    @property
    def success_rate(self) -> Decimal:
        """Відсоток успішних угод"""
        if self.total_trades == 0:
            return Decimal('0')
        return Decimal(self.successful_trades) / Decimal(self.total_trades) * Decimal('100')
    
    @property
    def net_profit(self) -> Decimal:
        """Чистий прибуток"""
        return self.total_profit - self.total_loss
    
    @property
    def profit_factor(self) -> Decimal:
        """Фактор прибутковості"""
        if self.total_loss == 0:
            return Decimal('0') if self.total_profit == 0 else Decimal('inf')
        return self.total_profit / self.total_loss
    
    def add_trade(self, 
                 token_address: str,
                 pnl: Decimal,
                 duration: int) -> None:
        """Додавання нової угоди до статистики"""
        self.total_trades += 1
        
        if pnl > 0:
            self.successful_trades += 1
            self.total_profit += pnl
        else:
            self.failed_trades += 1
            self.total_loss += abs(pnl)
            
        # Оновлення найкращої/найгіршої угоди
        self.best_trade_pnl = max(self.best_trade_pnl, pnl)
        self.worst_trade_pnl = min(self.worst_trade_pnl, pnl)
        
        # Оновлення середньої тривалості
        self.avg_trade_duration = (self.avg_trade_duration * (self.total_trades - 1) + duration) // self.total_trades
        
        # Оновлення продуктивності по токену
        if token_address in self.token_performance:
            self.token_performance[token_address] += pnl
        else:
            self.token_performance[token_address] = pnl
            
        self.period_end = datetime.now()
    
    def update_drawdown(self, current_drawdown: Decimal) -> None:
        """Оновлення максимальної просадки"""
        self.max_drawdown = min(self.max_drawdown, current_drawdown)
    
    def get_best_performing_tokens(self, limit: int = 5) -> List[tuple[str, Decimal]]:
        """Отримання найбільш прибуткових токенів"""
        return sorted(
            self.token_performance.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
    
    def get_worst_performing_tokens(self, limit: int = 5) -> List[tuple[str, Decimal]]:
        """Отримання найменш прибуткових токенів"""
        return sorted(
            self.token_performance.items(),
            key=lambda x: x[1]
        )[:limit] 