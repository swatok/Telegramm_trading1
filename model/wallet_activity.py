"""
Модель для представлення активності гаманця
"""
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from typing import Optional, Dict

@dataclass
class WalletActivity:
    wallet_address: str  # Адреса гаманця
    activity_type: str  # buy, sell, transfer, check, etc.
    token_address: str  # Адреса токену
    amount: Decimal  # Кількість токенів
    timestamp: datetime  # Час активності
    transaction_signature: str  # Підпис транзакції
    
    # Додаткова інформація
    price: Optional[Decimal] = None  # Ціна токену на момент активності
    counterparty: Optional[str] = None  # Адреса контрагента
    token_name: Optional[str] = None  # Назва токену
    token_symbol: Optional[str] = None  # Символ токену
    
    # Розширена інформація для свопів
    swap_info: Optional[Dict] = None  # Інформація про своп
    price_impact: Optional[Decimal] = None  # Вплив на ціну
    slippage: Optional[Decimal] = None  # Використаний slippage
    
    def __post_init__(self):
        """Валідація після створення"""
        valid_types = {'buy', 'sell', 'transfer', 'swap', 'mint', 'burn', 'check'}
        if self.activity_type not in valid_types:
            raise ValueError(f"Невірний тип активності: {self.activity_type}")
            
    @property
    def age_minutes(self) -> float:
        """Вік активності в хвилинах"""
        return (datetime.now() - self.timestamp).total_seconds() / 60
        
    @property
    def value_sol(self) -> Optional[Decimal]:
        """Вартість операції в SOL"""
        if self.price is None:
            return None
        return self.amount * self.price
        
    def to_dict(self) -> dict:
        """Конвертація в словник для збереження"""
        return {
            "wallet_address": self.wallet_address,
            "activity_type": self.activity_type,
            "token_address": self.token_address,
            "amount": str(self.amount),
            "timestamp": self.timestamp.isoformat(),
            "transaction_signature": self.transaction_signature,
            "price": str(self.price) if self.price else None,
            "counterparty": self.counterparty,
            "token_name": self.token_name,
            "token_symbol": self.token_symbol,
            "swap_info": self.swap_info,
            "price_impact": str(self.price_impact) if self.price_impact else None,
            "slippage": str(self.slippage) if self.slippage else None
        }
        
    def __str__(self) -> str:
        """Рядкове представлення активності"""
        token_info = self.token_symbol or self.token_name or self.token_address[:8]
        amount_str = f"{float(self.amount):.4f}"
        value_str = f" ({float(self.value_sol):.4f} SOL)" if self.value_sol else ""
        
        return (
            f"WalletActivity({self.activity_type.upper()}, {token_info}, "
            f"amount={amount_str}{value_str})"
        ) 