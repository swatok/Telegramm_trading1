"""Wallet interface"""

from abc import ABC, abstractmethod
from typing import Dict, List
from decimal import Decimal

class IWalletAPI(ABC):
    """Інтерфейс для взаємодії з гаманцем"""
    
    @abstractmethod
    async def get_balance(self, token_address: str = None) -> Decimal:
        """Отримання балансу"""
        pass
        
    @abstractmethod
    async def get_balances(self) -> Dict[str, Decimal]:
        """Отримання всіх балансів"""
        pass
        
    @abstractmethod
    async def get_portfolio_value(self) -> Dict:
        """Отримання вартості портфеля"""
        pass
        
    @abstractmethod
    async def get_transaction_history(self) -> List[Dict]:
        """Отримання історії транзакцій"""
        pass
        
    @abstractmethod
    async def sign_transaction(self, transaction: Dict) -> str:
        """Підписання транзакції"""
        pass
        
    @abstractmethod
    async def sign_and_send_transaction(self, transaction: Dict) -> str:
        """Підписання і відправка транзакції"""
        pass 