"""Market interface"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime

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