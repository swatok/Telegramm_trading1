"""DEX interface"""

from abc import ABC, abstractmethod
from typing import Dict, Optional
from decimal import Decimal

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