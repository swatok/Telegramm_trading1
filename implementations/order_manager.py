"""Order manager implementation"""

from typing import List, Optional, Dict
from decimal import Decimal
from datetime import datetime
import uuid

from interfaces.order_manager_interface import IOrderManager
from model.order import Order
from utils.calculators.gas_calculator import GasCalculator
from utils.calculators.slippage_calculator import SlippageCalculator

class OrderManager(IOrderManager):
    """Імплементація менеджера ордерів"""
    
    def __init__(self):
        self._orders: Dict[str, Order] = {}
        self._gas_calculator = GasCalculator()
        self._slippage_calculator = SlippageCalculator()
    
    async def create_order(self,
                          token_address: str,
                          amount: Decimal,
                          price: Decimal,
                          side: str,
                          order_type: str = 'market') -> Order:
        """Створення нового ордеру"""
        order_id = str(uuid.uuid4())
        order = Order(
            token_address=token_address,
            amount=amount,
            price=price,
            side=side,
            order_type=order_type
        )
        self._orders[order_id] = order
        return order
    
    async def cancel_order(self, order_id: str) -> bool:
        """Скасування ордеру"""
        if order_id not in self._orders:
            return False
            
        order = self._orders[order_id]
        if order.status in ['filled', 'cancelled']:
            return False
            
        order.update_status('cancelled')
        return True
    
    async def get_order(self, order_id: str) -> Optional[Order]:
        """Отримання інформації про ордер"""
        return self._orders.get(order_id)
    
    async def get_orders(self,
                        token_address: Optional[str] = None,
                        status: Optional[str] = None,
                        from_time: Optional[datetime] = None,
                        to_time: Optional[datetime] = None) -> List[Order]:
        """Отримання списку ордерів з фільтрацією"""
        orders = list(self._orders.values())
        
        if token_address:
            orders = [o for o in orders if o.token_address == token_address]
        if status:
            orders = [o for o in orders if o.status == status]
        if from_time:
            orders = [o for o in orders if o.created_at >= from_time]
        if to_time:
            orders = [o for o in orders if o.created_at <= to_time]
            
        return orders
    
    async def update_order(self,
                          order_id: str,
                          status: Optional[str] = None,
                          filled_amount: Optional[Decimal] = None,
                          filled_price: Optional[Decimal] = None) -> bool:
        """Оновлення інформації про ордер"""
        if order_id not in self._orders:
            return False
            
        order = self._orders[order_id]
        
        if status:
            order.update_status(status)
        if filled_amount and filled_price:
            order.fill(filled_amount, filled_price)
            
        return True
    
    async def get_active_orders(self) -> List[Order]:
        """Отримання списку активних ордерів"""
        return [o for o in self._orders.values() if o.status == 'pending']
    
    async def get_filled_orders(self,
                              from_time: Optional[datetime] = None,
                              to_time: Optional[datetime] = None) -> List[Order]:
        """Отримання списку виконаних ордерів"""
        orders = [o for o in self._orders.values() if o.status == 'filled']
        
        if from_time:
            orders = [o for o in orders if o.updated_at >= from_time]
        if to_time:
            orders = [o for o in orders if o.updated_at <= to_time]
            
        return orders
    
    async def get_cancelled_orders(self,
                                 from_time: Optional[datetime] = None,
                                 to_time: Optional[datetime] = None) -> List[Order]:
        """Отримання списку скасованих ордерів"""
        orders = [o for o in self._orders.values() if o.status == 'cancelled']
        
        if from_time:
            orders = [o for o in orders if o.updated_at >= from_time]
        if to_time:
            orders = [o for o in orders if o.updated_at <= to_time]
            
        return orders
    
    async def get_failed_orders(self,
                              from_time: Optional[datetime] = None,
                              to_time: Optional[datetime] = None) -> List[Order]:
        """Отримання списку невиконаних ордерів"""
        orders = [o for o in self._orders.values() if o.status == 'failed']
        
        if from_time:
            orders = [o for o in orders if o.updated_at >= from_time]
        if to_time:
            orders = [o for o in orders if o.updated_at <= to_time]
            
        return orders
    
    async def validate_order(self,
                           token_address: str,
                           amount: Decimal,
                           price: Decimal,
                           side: str) -> bool:
        """Валідація параметрів ордеру"""
        # Базова валідація
        if amount <= 0 or price <= 0:
            return False
            
        if side not in ['buy', 'sell']:
            return False
            
        # TODO: Додати більше перевірок (баланс, ліміти і т.д.)
        return True 