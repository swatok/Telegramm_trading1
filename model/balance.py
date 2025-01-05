"""
Модель для представлення балансу гаманця
"""
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from typing import Optional, Dict
from .token import Token

@dataclass
class Balance:
    wallet_address: str  # Адреса гаманця
    sol_balance: Decimal  # Баланс SOL
    last_updated: datetime  # Час останнього оновлення
    
    # Баланси токенів (адреса токену -> кількість)
    token_balances: Dict[str, Decimal] = None
    # Кешовані об'єкти токенів
    tokens: Dict[str, Token] = None
    
    def __post_init__(self):
        """Ініціалізація після створення"""
        if self.token_balances is None:
            self.token_balances = {}
        if self.tokens is None:
            self.tokens = {}
            
    def update_sol_balance(self, new_balance: Decimal):
        """Оновлення балансу SOL"""
        self.sol_balance = new_balance
        self.last_updated = datetime.now()
        
    def update_token_balance(self, token_address: str, amount: Decimal, token: Optional[Token] = None):
        """Оновлення балансу токену"""
        self.token_balances[token_address] = amount
        if token:
            self.tokens[token_address] = token
        self.last_updated = datetime.now()
        
    def get_token_balance(self, token_address: str) -> Optional[Decimal]:
        """Отримання балансу конкретного токену"""
        return self.token_balances.get(token_address)
        
    def get_token(self, token_address: str) -> Optional[Token]:
        """Отримання інформації про токен"""
        return self.tokens.get(token_address)
        
    def has_sufficient_sol(self, required_amount: Decimal) -> bool:
        """Перевірка достатності SOL"""
        return self.sol_balance >= required_amount
        
    def has_sufficient_token(self, token_address: str, required_amount: Decimal) -> bool:
        """Перевірка достатності токену"""
        token_balance = self.get_token_balance(token_address)
        if token_balance is None:
            return False
        return token_balance >= required_amount
        
    def to_dict(self) -> dict:
        """Конве��тація в словник для збереження"""
        return {
            "wallet_address": self.wallet_address,
            "sol_balance": str(self.sol_balance),
            "last_updated": self.last_updated.isoformat(),
            "token_balances": {
                addr: str(amount)
                for addr, amount in self.token_balances.items()
            },
            "tokens": {
                addr: token.to_dict()
                for addr, token in self.tokens.items()
            }
        }
        
    def __str__(self) -> str:
        """Рядкове представлення балансу"""
        token_count = len(self.token_balances)
        return (
            f"Balance({self.wallet_address[:4]}...{self.wallet_address[-4:]}): "
            f"{self.sol_balance:.4f} SOL, {token_count} tokens"
        ) 