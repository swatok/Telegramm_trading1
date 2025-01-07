"""Order model"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any

@dataclass
class Order:
    """Клас для представлення торгового ордеру"""
    token_address: str
    amount: Decimal
    price: Decimal
    side: str  # 'buy' or 'sell'
    order_type: str  # 'market' or 'limit'
    status: str = 'pending'
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    filled_amount: Decimal = Decimal('0')
    filled_price: Optional[Decimal] = None
    gas_price: Optional[Decimal] = None
    gas_used: Optional[int] = None
    transaction_hash: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_filled(self) -> bool:
        """Перевірка чи ордер повністю виконано"""
        return self.filled_amount == self.amount
    
    @property
    def remaining_amount(self) -> Decimal:
        """Залишок для виконання"""
        return self.amount - self.filled_amount
    
    @property
    def value(self) -> Decimal:
        """Загальна вартість ордеру"""
        return self.amount * self.price
    
    @property
    def filled_value(self) -> Decimal:
        """Вартість виконаної частини"""
        if self.filled_price:
            return self.filled_amount * self.filled_price
        return Decimal('0')
    
    def update_status(self, status: str, error: Optional[str] = None) -> None:
        """Оновлення статусу ордеру"""
        self.status = status
        self.error = error
        self.updated_at = datetime.now()
    
    def fill(self, amount: Decimal, price: Decimal) -> None:
        """Виконання частини або всього ордеру"""
        self.filled_amount += amount
        self.filled_price = price
        self.updated_at = datetime.now()
        
        if self.is_filled:
            self.status = 'filled'
    
    def set_transaction_details(self, 
                              tx_hash: str,
                              gas_price: Decimal,
                              gas_used: int) -> None:
        """Встановлення деталей транзакції"""
        self.transaction_hash = tx_hash
        self.gas_price = gas_price
        self.gas_used = gas_used
        self.updated_at = datetime.now()
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Додавання метаданих"""
        self.metadata[key] = value
        self.updated_at = datetime.now() 