"""Order service implementation"""

from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime

from interfaces.order_interface import IOrderService
from implementations.api.dex_api import DexAPI
from model.order import Order

class OrderService(IOrderService):
    """Сервіс для управління ордерами"""
    
    def __init__(self, dex_api: DexAPI):
        self._dex_api = dex_api
        self._active_orders: Dict[str, Order] = {}
        
    async def create_order(self,
                         token_address: str,
                         amount: Decimal,
                         price: Decimal,
                         side: str,
                         order_type: str,
                         max_slippage: Optional[Decimal] = None) -> Order:
        """Створення ордеру"""
        order = Order(
            token_address=token_address,
            amount=amount,
            price=price,
            side=side,
            order_type=order_type,
            max_slippage=max_slippage,
            status='pending',
            timestamp=datetime.now()
        )
        
        if order_type == 'market':
            return await self._execute_market_order(order)
        else:
            self._active_orders[order.id] = order
            return order
            
    async def _execute_market_order(self, order: Order) -> Order:
        """Виконання ринкового ордеру"""
        try:
            # Отримуємо актуальну ціну
            current_price = await self._dex_api.get_token_price(order.token_address)
            
            # Перевіряємо проковзування
            if order.max_slippage:
                if order.side == 'buy':
                    max_price = order.price * (1 + order.max_slippage)
                    if current_price > max_price:
                        order.status = 'failed'
                        order.error = 'Price slippage too high'
                        return order
                else:
                    min_price = order.price * (1 - order.max_slippage)
                    if current_price < min_price:
                        order.status = 'failed'
                        order.error = 'Price slippage too high'
                        return order
                        
            # Виконуємо ордер
            result = await self._dex_api.execute_swap(
                token_address=order.token_address,
                amount=order.amount,
                side=order.side,
                price=current_price
            )
            
            if result['success']:
                order.status = 'filled'
                order.filled_price = current_price
                order.filled_amount = order.amount
                order.transaction_hash = result['transaction_hash']
            else:
                order.status = 'failed'
                order.error = result['error']
                
        except Exception as e:
            order.status = 'failed'
            order.error = str(e)
            
        return order
        
    async def cancel_order(self, order_id: str) -> bool:
        """Скасування ордеру"""
        if order_id not in self._active_orders:
            return False
            
        order = self._active_orders[order_id]
        if order.order_type == 'market':
            return False
            
        order.status = 'cancelled'
        del self._active_orders[order_id]
        return True
        
    async def get_order_status(self, order_id: str) -> Dict:
        """Отримання статусу ордеру"""
        if order_id not in self._active_orders:
            return {'status': 'not_found'}
            
        order = self._active_orders[order_id]
        return {
            'status': order.status,
            'filled_price': order.filled_price,
            'filled_amount': order.filled_amount,
            'error': order.error
        }
        
    async def get_active_orders(self) -> List[Order]:
        """Отримання списку активних ордерів"""
        return list(self._active_orders.values())
        
    async def get_filled_orders(self,
                              from_time: Optional[datetime] = None,
                              to_time: Optional[datetime] = None) -> List[Order]:
        """Отримання списку виконаних ордерів"""
        # TODO: Додати збереження історії ордерів в базу даних
        return [] 