"""
Модель для управління торговими позиціями
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Set

@dataclass
class Position:
    # Базові поля
    token_address: str
    initial_amount: Decimal
    entry_price: Decimal
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Поточний стан
    remaining_amount: Decimal = field(init=False)
    current_price: Optional[Decimal] = None
    pnl: Optional[Decimal] = None
    
    # Take-profit і Stop-loss
    take_profit_levels: List[Dict[str, Decimal]] = field(default_factory=list)
    stop_loss_level: Optional[Decimal] = None
    triggered_levels: Set[Decimal] = field(default_factory=set)
    take_profit_hits: List[Dict] = field(default_factory=list)
    stop_loss_hit: bool = False
    
    # Історія та статус
    exit_history: Dict = field(default_factory=dict)
    is_active: bool = True
    close_price: Optional[Decimal] = None
    close_time: Optional[datetime] = None
    
    def __post_init__(self):
        """Ініціалізація після створення"""
        self.remaining_amount = self.initial_amount
        
    def update_price(self, new_price: Decimal) -> None:
        """Оновлення поточної ціни та розрахунок P&L"""
        self.current_price = new_price
        if self.entry_price:
            self.pnl = ((new_price - self.entry_price) / self.entry_price) * Decimal("100")
            
    def check_take_profit(self) -> Optional[Dict]:
        """
        Перевірка досягнення take-profit рівнів
        Returns:
            Dict з інформацією про досягнутий рівень або None
        """
        if not self.current_price or not self.take_profit_levels:
            return None
            
        for level in self.take_profit_levels:
            if (self.pnl >= level['level'] and 
                level['level'] not in [hit['level'] for hit in self.take_profit_hits]):
                hit_info = {
                    'level': level['level'],
                    'price': self.current_price,
                    'time': datetime.now()
                }
                self.take_profit_hits.append(hit_info)
                return hit_info
        return None
        
    def check_stop_loss(self) -> bool:
        """
        Перевірка досягнення stop-loss рівня
        Returns:
            True якщо stop-loss досягнуто
        """
        if not self.pnl or not self.stop_loss_level:
            return False
            
        if self.pnl <= self.stop_loss_level and not self.stop_loss_hit:
            self.stop_loss_hit = True
            return True
        return False
        
    def close_position(self, close_price: Decimal, reason: str) -> None:
        """Закриття позиції"""
        self.is_active = False
        self.close_price = close_price
        self.close_time = datetime.now()
        self.update_price(close_price)
        self.add_exit(self.remaining_amount, close_price, reason)
        self.remaining_amount = Decimal("0")
        
    def add_exit(self, amount: Decimal, price: Decimal, reason: str) -> None:
        """Додати запис про вихід з позиції"""
        self.exit_history[datetime.now()] = {
            "amount": amount,
            "price": price,
            "reason": reason
        }
        self.remaining_amount -= amount
        
    def to_dict(self) -> dict:
        """Конвертація в словник для збереження"""
        return {
            "token_address": self.token_address,
            "initial_amount": str(self.initial_amount),
            "entry_price": str(self.entry_price),
            "timestamp": self.timestamp.isoformat(),
            "remaining_amount": str(self.remaining_amount),
            "current_price": str(self.current_price) if self.current_price else None,
            "pnl": str(self.pnl) if self.pnl else None,
            "take_profit_hits": [
                {
                    "level": str(hit["level"]),
                    "price": str(hit["price"]),
                    "time": hit["time"].isoformat()
                }
                for hit in self.take_profit_hits
            ],
            "stop_loss_hit": self.stop_loss_hit,
            "triggered_levels": [str(level) for level in self.triggered_levels],
            "exit_history": {
                k.isoformat(): {
                    "amount": str(v["amount"]),
                    "price": str(v["price"]),
                    "reason": v["reason"]
                }
                for k, v in self.exit_history.items()
            },
            "is_active": self.is_active,
            "close_price": str(self.close_price) if self.close_price else None,
            "close_time": self.close_time.isoformat() if self.close_time else None
        }
        
    def __str__(self) -> str:
        """Рядкове представлення позиції"""
        status = "active" if self.is_active else "closed"
        pnl_str = f", PNL={self.pnl:.2f}%" if self.pnl is not None else ""
        return (
            f"Position({self.token_address}, {self.remaining_amount}, "
            f"entry_price={self.entry_price}, {status}{pnl_str})"
        ) 