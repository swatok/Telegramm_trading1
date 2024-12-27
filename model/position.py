"""
Модель для управління торговими позиціями
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Dict, Set

@dataclass
class Position:
    token_address: str
    initial_amount: Decimal
    initial_value: Decimal  # в SOL
    entry_price: Decimal
    timestamp: datetime
    
    # Поточний стан
    remaining_amount: Decimal = field(init=False)
    triggered_levels: Set[Decimal] = field(default_factory=set)
    exit_history: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Ініціалізація після створення"""
        self.remaining_amount = self.initial_amount
        
    def is_level_triggered(self, level: Decimal) -> bool:
        """Перевірка чи рівень вже був активований"""
        return level in self.triggered_levels
        
    def mark_level_triggered(self, level: Decimal):
        """Позначити рівень як активований"""
        self.triggered_levels.add(level)
        
    def add_exit(self, amount: Decimal, price: Decimal, reason: str):
        """Додати запис про частковий вихід"""
        self.exit_history[datetime.now()] = {
            "amount": amount,
            "price": price,
            "reason": reason
        }
        
    @property
    def is_closed(self) -> bool:
        """Чи закрита позиція"""
        return self.remaining_amount <= Decimal("0")
        
    def to_dict(self) -> dict:
        """Конвертація в словник для збереження"""
        return {
            "token_address": self.token_address,
            "initial_amount": str(self.initial_amount),
            "initial_value": str(self.initial_value),
            "entry_price": str(self.entry_price),
            "timestamp": self.timestamp.isoformat(),
            "remaining_amount": str(self.remaining_amount),
            "triggered_levels": [str(level) for level in self.triggered_levels],
            "exit_history": {
                k.isoformat(): {
                    "amount": str(v["amount"]),
                    "price": str(v["price"]),
                    "reason": v["reason"]
                }
                for k, v in self.exit_history.items()
            }
        }
        
    def __str__(self) -> str:
        """Рядкове представлення позиції"""
        return (
            f"Position({self.token_address}, {self.remaining_amount}, "
            f"entry_price={self.entry_price}, timestamp={self.timestamp})"
        ) 