"""Order executor interface"""

from abc import ABC, abstractmethod
from typing import Dict, Optional
from decimal import Decimal
from model.order import Order

class IOrderExecutor(ABC):
    """Інтерфейс для виконання ордерів"""
    
    @abstractmethod
    async def execute_order(self,
                          order: Order,
                          max_slippage: Optional[Decimal] = None) -> bool:
        """Виконання ордеру"""
        pass
        
    @abstractmethod
    async def estimate_execution_price(self,
                                     token_address: str,
                                     amount: Decimal,
                                     side: str) -> Decimal:
        """Оцінка ціни виконання"""
        pass
        
    @abstractmethod
    async def estimate_execution_fee(self,
                                   token_address: str,
                                   amount: Decimal) -> Dict[str, Decimal]:
        """Оцінка комісії за виконання"""
        pass
        
    @abstractmethod
    async def validate_execution(self,
                               order: Order,
                               max_slippage: Optional[Decimal] = None) -> bool:
        """Валідація можливості виконання"""
        pass
        
    @abstractmethod
    async def get_execution_status(self,
                                 order: Order) -> str:
        """Отримання статусу виконання"""
        pass
        
    @abstractmethod
    async def cancel_execution(self,
                             order: Order) -> bool:
        """Скасування виконання"""
        pass 