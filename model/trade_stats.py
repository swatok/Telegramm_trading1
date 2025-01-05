"""
Модель для представлення торгової статистики
"""
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Optional, Dict, List

@dataclass
class TradeStats:
    period: str  # day, week, month, all
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # Основна статистика
    total_trades: int = 0
    successful_trades: int = 0
    failed_trades: int = 0
    total_volume: Decimal = Decimal("0")
    total_profit: Decimal = Decimal("0")
    total_fees: Decimal = Decimal("0")
    
    # Розширена статистика
    avg_trade_size: Decimal = Decimal("0")
    avg_profit_per_trade: Decimal = Decimal("0")
    max_profit: Decimal = Decimal("0")
    max_loss: Decimal = Decimal("0")
    win_rate: float = 0.0
    
    # Статистика по токенах
    token_stats: Dict[str, Dict] = field(default_factory=dict)
    
    # Часова статистика
    hourly_distribution: Dict[int, int] = field(default_factory=dict)
    daily_distribution: Dict[str, int] = field(default_factory=dict)
    
    def __post_init__(self):
        """Валідація після створення"""
        valid_periods = {'day', 'week', 'month', 'all'}
        if self.period not in valid_periods:
            raise ValueError(f"Невірний період: {self.period}")
            
        if not self.end_time:
            self.end_time = datetime.now()
            
    @property
    def duration_hours(self) -> float:
        """Тривалість періоду в годинах"""
        return (self.end_time - self.start_time).total_seconds() / 3600
        
    @property
    def trades_per_hour(self) -> float:
        """Кількість угод на годину"""
        if self.duration_hours == 0:
            return 0.0
        return self.total_trades / self.duration_hours
        
    def add_trade(self, token: str, amount: Decimal, profit: Decimal, 
                 fees: Decimal, timestamp: datetime, success: bool):
        """Додавання нової угоди в статистику"""
        # Оновлення основної статистики
        self.total_trades += 1
        self.total_volume += amount
        self.total_profit += profit
        self.total_fees += fees
        
        if success:
            self.successful_trades += 1
        else:
            self.failed_trades += 1
            
        # Оновлення розширеної статистики
        self.avg_trade_size = self.total_volume / self.total_trades
        self.avg_profit_per_trade = self.total_profit / self.total_trades
        self.max_profit = max(self.max_profit, profit)
        self.max_loss = min(self.max_loss, profit)
        self.win_rate = (self.successful_trades / self.total_trades) * 100
        
        # Оновлення статистики по токенах
        if token not in self.token_stats:
            self.token_stats[token] = {
                "trades": 0,
                "volume": Decimal("0"),
                "profit": Decimal("0"),
                "success_rate": 0.0
            }
            
        token_stat = self.token_stats[token]
        token_stat["trades"] += 1
        token_stat["volume"] += amount
        token_stat["profit"] += profit
        token_stat["success_rate"] = (
            sum(1 for t in self.token_stats[token].get("trades_success", []) if t) / 
            token_stat["trades"] * 100
        )
        
        # Оновлення часової статистики
        hour = timestamp.hour
        self.hourly_distribution[hour] = self.hourly_distribution.get(hour, 0) + 1
        
        day = timestamp.strftime("%A")
        self.daily_distribution[day] = self.daily_distribution.get(day, 0) + 1
        
    def get_best_performing_tokens(self, limit: int = 5) -> List[Dict]:
        """Отримання найбільш прибуткових токенів"""
        sorted_tokens = sorted(
            self.token_stats.items(),
            key=lambda x: x[1]["profit"],
            reverse=True
        )
        return [
            {"token": token, **stats}
            for token, stats in sorted_tokens[:limit]
        ]
        
    def get_best_trading_hours(self, limit: int = 5) -> List[Dict]:
        """Отримання найкращих годин для торгівлі"""
        sorted_hours = sorted(
            self.hourly_distribution.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return [
            {"hour": hour, "trades": count}
            for hour, count in sorted_hours[:limit]
        ]
        
    def to_dict(self) -> dict:
        """Конвертація в словник для збереження"""
        return {
            "period": self.period,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_trades": self.total_trades,
            "successful_trades": self.successful_trades,
            "failed_trades": self.failed_trades,
            "total_volume": str(self.total_volume),
            "total_profit": str(self.total_profit),
            "total_fees": str(self.total_fees),
            "avg_trade_size": str(self.avg_trade_size),
            "avg_profit_per_trade": str(self.avg_profit_per_trade),
            "max_profit": str(self.max_profit),
            "max_loss": str(self.max_loss),
            "win_rate": self.win_rate,
            "token_stats": {
                token: {
                    **{k: str(v) if isinstance(v, Decimal) else v 
                       for k, v in stats.items()}
                }
                for token, stats in self.token_stats.items()
            },
            "hourly_distribution": self.hourly_distribution,
            "daily_distribution": self.daily_distribution
        }
        
    def __str__(self) -> str:
        """Рядкове представлення статистики"""
        return (
            f"TradeStats({self.period}, trades={self.total_trades}, "
            f"profit={float(self.total_profit):.2f}, win_rate={self.win_rate:.1f}%)"
        ) 