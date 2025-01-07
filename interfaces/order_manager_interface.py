"""Order manager interface"""

from abc import ABC, abstractmethod
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from model.order import Order

class IOrderManager(ABC):
    """Інтерфейс для управління ордерами"""
    
    @abstractmethod
    async def create_order(self,
                          token_address: str,
                          amount: Decimal,
                          price: Decimal,
                          side: str,
                          order_type: str = 'market') -> Order:
        """Створення нового ордеру"""
        pass
        
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Скасування ордеру"""
        pass
        
    @abstractmethod
    async def get_order(self, order_id: str) -> Optional[Order]:
        """Отримання інформації про ордер"""
        pass
        
    @abstractmethod
    async def get_orders(self,
                        token_address: Optional[str] = None,
                        status: Optional[str] = None,
                        from_time: Optional[datetime] = None,
                        to_time: Optional[datetime] = None) -> List[Order]:
        """Отримання списку ордерів з фільтрацією"""
        pass
        
    @abstractmethod
    async def update_order(self,
                          order_id: str,
                          status: Optional[str] = None,
                          filled_amount: Optional[Decimal] = None,
                          filled_price: Optional[Decimal] = None) -> bool:
        """Оновлення інформації про ордер"""
        pass
        
    @abstractmethod
    async def get_active_orders(self) -> List[Order]:
        """Отримання списку активних ордерів"""
        pass
        
    @abstractmethod
    async def get_filled_orders(self,
                              from_time: Optional[datetime] = None,
                              to_time: Optional[datetime] = None) -> List[Order]:
        """Отримання списку виконаних ордерів"""
        pass
        
    @abstractmethod
    async def get_cancelled_orders(self,
                                 from_time: Optional[datetime] = None,
                                 to_time: Optional[datetime] = None) -> List[Order]:
        """Отримання списку скасованих ордерів"""
        pass
        
    @abstractmethod
    async def get_failed_orders(self,
                              from_time: Optional[datetime] = None,
                              to_time: Optional[datetime] = None) -> List[Order]:
        """Отримання списку невиконаних ордерів"""
        pass
        
    @abstractmethod
    async def validate_order(self,
                           token_address: str,
                           amount: Decimal,
                           price: Decimal,
                           side: str) -> bool:
        """Валідація параметрів ордеру"""
        pass 