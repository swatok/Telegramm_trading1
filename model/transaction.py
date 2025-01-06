"""
Модель для представлення транзакцій в мережі Solana
"""
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from typing import Optional, Dict

@dataclass
class Transaction:
    signature: str  # Підпис транзакції
    status: str  # confirmed, failed, pending
    timestamp: datetime
    token_address: str
    amount: Decimal
    type: str  # swap, transfer, etc.
    
    # Додаткова інформація
    confirmations: int = 0
    balance_change: Optional[Decimal] = None
    error: Optional[str] = None
    gas_used: Optional[Decimal] = None
    block_number: Optional[int] = None
    
    # Розширена інформація для свопів
    swap_info: Optional[Dict] = None  # Деталі свопу (route, impact, etc.)
    input_amount: Optional[Decimal] = None
    output_amount: Optional[Decimal] = None
    price_impact: Optional[Decimal] = None
    
    def __post_init__(self):
        """Валідація після створення"""
        valid_statuses = {'confirmed', 'failed', 'pending'}
        if self.status not in valid_statuses:
            raise ValueError(f"Невірний статус транзакції: {self.status}")
            
    @property
    def is_confirmed(self) -> bool:
        """Чи підтверджена транзакція"""
        return self.status == 'confirmed'
        
    @property
    def age_seconds(self) -> float:
        """Вік транзакції в секундах"""
        return (datetime.now() - self.timestamp).total_seconds()
        
    def to_dict(self) -> dict:
        """Конвертація в словник для збереження"""
        return {
            "signature": self.signature,
            "status": self.status,
            "timestamp": self.timestamp.isoformat(),
            "token_address": self.token_address,
            "amount": str(self.amount),
            "type": self.type,
            "confirmations": self.confirmations,
            "balance_change": str(self.balance_change) if self.balance_change else None,
            "error": self.error,
            "gas_used": str(self.gas_used) if self.gas_used else None,
            "block_number": self.block_number,
            "swap_info": self.swap_info,
            "input_amount": str(self.input_amount) if self.input_amount else None,
            "output_amount": str(self.output_amount) if self.output_amount else None,
            "price_impact": str(self.price_impact) if self.price_impact else None
        }
        
    def __str__(self) -> str:
        """Рядкове представлення транзакції"""
        return (
            f"Transaction({self.signature[:8]}..., {self.type}, "
            f"status={self.status}, amount={float(self.amount):.4f})"
        ) 