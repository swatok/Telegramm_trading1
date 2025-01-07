"""Market data interface"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime

class IMarketDataProvider(ABC):
    """Інтерфейс для отримання ринкових даних"""
    
    @abstractmethod
    async def get_price(self,
                       token_address: str) -> Decimal:
        """Отримання поточної ціни токена"""
        pass
        
    @abstractmethod
    async def get_liquidity(self,
                           token_address: str) -> Decimal:
        """Отримання ліквідності токена"""
        pass
        
    @abstractmethod
    async def get_historical_prices(self,
                                  token_address: str,
                                  from_time: datetime,
                                  to_time: datetime) -> List[Dict[str, Decimal]]:
        """Отримання історичних цін"""
        pass
        
    @abstractmethod
    async def get_price_change(self,
                             token_address: str,
                             time_frame: str) -> Decimal:
        """Отримання зміни ціни за період"""
        pass
        
    @abstractmethod
    async def get_market_depth(self,
                             token_address: str,
                             levels: int = 10) -> Dict[str, List[Dict[str, Decimal]]]:
        """Отримання глибини ринку"""
        pass
        
    @abstractmethod
    async def get_volatility(self,
                           token_address: str,
                           time_frame: str) -> Decimal:
        """Отримання волатильності"""
        pass
        
    @abstractmethod
    async def get_trading_volume(self,
                               token_address: str,
                               time_frame: str) -> Decimal:
        """Отримання об'єму торгів"""
        pass
        
    @abstractmethod
    async def get_market_impact(self,
                              token_address: str,
                              amount: Decimal) -> Decimal:
        """Розрахунок впливу на ринок"""
        pass 