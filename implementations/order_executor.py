"""Order executor implementation"""

from typing import Dict, Optional
from decimal import Decimal

from interfaces.order_executor_interface import IOrderExecutor
from model.order import Order
from utils.calculators.gas_calculator import GasCalculator
from utils.calculators.slippage_calculator import SlippageCalculator

class OrderExecutor(IOrderExecutor):
    """Імплементація виконавця ордерів"""
    
    def __init__(self):
        self._gas_calculator = GasCalculator()
        self._slippage_calculator = SlippageCalculator()
        self._executions: Dict[str, Dict] = {}  # order_id -> execution_details
    
    async def execute_order(self,
                          order: Order,
                          max_slippage: Optional[Decimal] = None) -> bool:
        """Виконання ордеру"""
        # Валідація виконання
        if not await self.validate_execution(order, max_slippage):
            return False
            
        try:
            # Оцінка ціни виконання
            execution_price = await self.estimate_execution_price(
                order.token_address,
                order.amount,
                order.side
            )
            
            # Оцінка комісії
            fees = await self.estimate_execution_fee(
                order.token_address,
                order.amount
            )
            
            # Зберігаємо деталі виконання
            self._executions[id(order)] = {
                'execution_price': execution_price,
                'fees': fees,
                'status': 'executing'
            }
            
            # TODO: Додати реальне виконання через DEX
            
            # Оновлюємо статус
            order.fill(order.amount, execution_price)
            self._executions[id(order)]['status'] = 'completed'
            
            return True
            
        except Exception as e:
            order.update_status('failed', str(e))
            self._executions[id(order)] = {
                'status': 'failed',
                'error': str(e)
            }
            return False
    
    async def estimate_execution_price(self,
                                     token_address: str,
                                     amount: Decimal,
                                     side: str) -> Decimal:
        """Оцінка ціни виконання"""
        # TODO: Додати реальне отримання ціни з DEX
        base_price = Decimal('1.0')  # Тимчасово
        
        # Розрахунок проковзування
        slippage = self._slippage_calculator.estimate_slippage(
            token_address=token_address,
            amount=amount,
            liquidity=Decimal('1000000')  # TODO: Отримати реальну ліквідність
        )
        
        # Застосування проковзування
        if side == 'buy':
            return base_price * (1 + slippage / 100)
        return base_price * (1 - slippage / 100)
    
    async def estimate_execution_fee(self,
                                   token_address: str,
                                   amount: Decimal) -> Dict[str, Decimal]:
        """Оцінка комісії за виконання"""
        # Оцінка газу
        gas_price = self._gas_calculator.estimate_gas_price(
            network_load=0.5,  # TODO: Отримати реальне навантаження
            priority='normal'
        )
        
        gas_limit = self._gas_calculator.estimate_gas_limit(
            operation_type='swap',
            token_address=token_address,
            amount=amount
        )
        
        gas_cost = self._gas_calculator.calculate_total_gas_cost(
            gas_price=gas_price,
            gas_limit=gas_limit
        )
        
        return {
            'gas_price': gas_price,
            'gas_limit': Decimal(str(gas_limit)),
            'gas_cost': gas_cost,
            'dex_fee': amount * Decimal('0.003')  # 0.3% комісія DEX
        }
    
    async def validate_execution(self,
                               order: Order,
                               max_slippage: Optional[Decimal] = None) -> bool:
        """Валідація можливості виконання"""
        if order.status != 'pending':
            return False
            
        # Перевірка проковзування
        if max_slippage:
            estimated_slippage = self._slippage_calculator.estimate_slippage(
                token_address=order.token_address,
                amount=order.amount,
                liquidity=Decimal('1000000')  # TODO: Отримати реальну ліквідність
            )
            if estimated_slippage > max_slippage:
                return False
        
        # TODO: Додати більше перевірок
        return True
    
    async def get_execution_status(self,
                                 order: Order) -> str:
        """Отримання статусу виконання"""
        if id(order) not in self._executions:
            return 'not_started'
        return self._executions[id(order)]['status']
    
    async def cancel_execution(self,
                             order: Order) -> bool:
        """Скасування виконання"""
        if id(order) not in self._executions:
            return False
            
        execution = self._executions[id(order)]
        if execution['status'] != 'executing':
            return False
            
        # TODO: Додати реальне скасування в DEX
        
        execution['status'] = 'cancelled'
        order.update_status('cancelled')
        return True 