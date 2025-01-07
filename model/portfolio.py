"""Portfolio model"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from decimal import Decimal

@dataclass
class Portfolio:
    """Клас для представлення портфеля користувача"""
    wallet_address: str
    total_value: Decimal = Decimal('0')
    positions: Dict[str, 'Position'] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_position(self, position: 'Position') -> None:
        """Додавання нової позиції"""
        self.positions[position.token_address] = position
        self.update_total_value()
        self.updated_at = datetime.now()
    
    def remove_position(self, token_address: str) -> None:
        """Видалення позиції"""
        if token_address in self.positions:
            del self.positions[token_address]
            self.update_total_value()
            self.updated_at = datetime.now()
    
    def update_total_value(self) -> None:
        """Оновлення загальної вартості портфеля"""
        self.total_value = sum(position.current_value for position in self.positions.values())
        self.updated_at = datetime.now()
    
    def get_position(self, token_address: str) -> Optional['Position']:
        """Отримання позиції за адресою токена"""
        return self.positions.get(token_address)
    
    def get_all_positions(self) -> List['Position']:
        """Отримання всіх позицій"""
        return list(self.positions.values()) 