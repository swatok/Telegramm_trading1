"""Wallet model"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

@dataclass
class Wallet:
    """Клас для представлення гаманця"""
    address: str
    balances: Dict[str, Decimal] = field(default_factory=dict)  # token_address -> amount
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_transaction: Optional[datetime] = None
    is_active: bool = True
    labels: List[str] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)
    
    def update_balance(self, token_address: str, amount: Decimal) -> None:
        """Оновлення балансу токену"""
        self.balances[token_address] = amount
        self.updated_at = datetime.now()
    
    def get_balance(self, token_address: str) -> Decimal:
        """Отримання балансу токену"""
        return self.balances.get(token_address, Decimal('0'))
    
    def add_transaction(self, timestamp: datetime) -> None:
        """Додавання інформації про транзакцію"""
        self.last_transaction = timestamp
        self.updated_at = datetime.now()
    
    def add_label(self, label: str) -> None:
        """Додавання мітки до гаманця"""
        if label not in self.labels:
            self.labels.append(label)
            self.updated_at = datetime.now()
    
    def remove_label(self, label: str) -> None:
        """Видалення мітки з гаманця"""
        if label in self.labels:
            self.labels.remove(label)
            self.updated_at = datetime.now()
    
    def set_metadata(self, key: str, value: str) -> None:
        """Встановлення метаданих"""
        self.metadata[key] = value
        self.updated_at = datetime.now()
    
    def deactivate(self) -> None:
        """Деактивація гаманця"""
        self.is_active = False
        self.updated_at = datetime.now()
    
    def activate(self) -> None:
        """Активація гаманця"""
        self.is_active = True
        self.updated_at = datetime.now()
    
    @property
    def total_tokens(self) -> int:
        """Кількість різних токенів в гаманці"""
        return len([amount for amount in self.balances.values() if amount > 0])
    
    @property
    def has_activity(self) -> bool:
        """Перевірка чи був рух по гаманцю"""
        return self.last_transaction is not None 