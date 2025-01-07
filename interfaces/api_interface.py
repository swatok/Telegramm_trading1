"""API interfaces"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime

class IDexAPI(ABC):
    """Інтерфейс для взаємодії з DEX"""
    
    @abstractmethod
    async def get_token_price(self, token_address: str) -> Decimal:
        """Отримання ціни токена"""
        pass
        
    @abstractmethod
    async def get_token_info(self, token_address: str) -> Dict:
        """Отримання інформації про токен"""
        pass
        
    @abstractmethod
    async def execute_swap(self,
                         token_address: str,
                         amount: Decimal,
                         side: str,
                         price: Optional[Decimal] = None,
                         slippage: Optional[Decimal] = None) -> Dict:
        """Виконання свопу"""
        pass
        
    @abstractmethod
    async def get_liquidity_pools(self, token_address: str) -> Dict:
        """Отримання інформації про пули ліквідності"""
        pass
        
    @abstractmethod
    async def get_market_depth(self, token_address: str) -> Dict:
        """Отримання глибини ринку"""
        pass
        
class IMarketAPI(ABC):
    """Інтерфейс для отримання ринкових даних"""
    
    @abstractmethod
    async def get_token_price(self, token_address: str) -> Decimal:
        """Отримання ціни токена"""
        pass
        
    @abstractmethod
    async def get_token_info(self, token_address: str) -> Dict:
        """Отримання інформації про токен"""
        pass
        
    @abstractmethod
    async def get_market_summary(self, token_address: str) -> Dict:
        """Отримання зведення по ринку"""
        pass
        
    @abstractmethod
    async def get_price_history(self,
                              token_address: str,
                              from_time: Optional[datetime] = None,
                              to_time: Optional[datetime] = None,
                              interval: str = '1h') -> List[Dict]:
        """Отримання історії цін"""
        pass
        
    @abstractmethod
    async def get_top_tokens(self, limit: int = 100) -> List[Dict]:
        """Отримання топ токенів за об'ємом"""
        pass
        
    @abstractmethod
    async def get_market_alerts(self, token_address: str) -> List[Dict]:
        """Отримання ринкових алертів"""
        pass
        
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
