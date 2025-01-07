"""Order calculator utilities"""

from decimal import Decimal
from typing import Dict, Optional
from model.order import Order

class OrderCalculator:
    """Калькулятор для розрахунків пов'язаних з ордерами"""
    
    @staticmethod
    def calculate_slippage(expected_price: Decimal,
                          actual_price: Decimal) -> Decimal:
        """Розрахунок проковзування"""
        return abs(actual_price - expected_price) / expected_price * Decimal('100')
    
    @staticmethod
    def calculate_gas_cost(gas_price: Decimal,
                          gas_used: int) -> Decimal:
        """Розрахунок вартості газу"""
        return gas_price * Decimal(str(gas_used))
    
    @staticmethod
    def calculate_total_cost(order: Order) -> Optional[Decimal]:
        """Розрахунок повної вартості ордеру з урахуванням газу"""
        if not order.gas_price or not order.gas_used:
            return None
            
        gas_cost = OrderCalculator.calculate_gas_cost(order.gas_price, order.gas_used)
        return order.filled_value + gas_cost
    
    @staticmethod
    def calculate_price_impact(market_price: Decimal,
                             execution_price: Decimal) -> Decimal:
        """Розрахунок впливу на ціну"""
        return (execution_price - market_price) / market_price * Decimal('100')
    
    @staticmethod
    def estimate_gas_limit(token_address: str,
                          amount: Decimal,
                          historical_data: Dict) -> int:
        """Оцінка ліміту газу на основі історичних даних"""
        base_gas = 150000  # Базовий ліміт газу для Solana DEX
        
        # Множники для корекції ліміту газу
        size_multiplier = Decimal('1.0')
        if amount > Decimal('10.0'):
            size_multiplier = Decimal('1.2')
        elif amount > Decimal('100.0'):
            size_multiplier = Decimal('1.5')
            
        # Історичний множник
        historical_multiplier = Decimal('1.0')
        if token_address in historical_data:
            avg_gas = historical_data[token_address].get('average_gas_used', base_gas)
            historical_multiplier = Decimal(str(avg_gas)) / Decimal(str(base_gas))
            
        final_gas = int(base_gas * size_multiplier * historical_multiplier)
        return min(final_gas, 300000)  # Максимальний ліміт
    
    @staticmethod
    def calculate_priority_fee(base_fee: Decimal,
                             urgency: str = 'normal') -> Decimal:
        """Розрахунок пріоритетної комісії"""
        multipliers = {
            'low': Decimal('1.1'),
            'normal': Decimal('1.3'),
            'high': Decimal('1.5'),
            'urgent': Decimal('2.0')
        }
        return base_fee * multipliers.get(urgency, Decimal('1.3'))
    
    @staticmethod
    def estimate_execution_price(order_amount: Decimal,
                               pool_liquidity: Decimal,
                               current_price: Decimal) -> Decimal:
        """Оцінка ціни виконання з урахуванням розміру ордеру та ліквідності"""
        impact = (order_amount / pool_liquidity) * Decimal('0.5')
        if impact > Decimal('0.1'):
            impact = Decimal('0.1')  # Максимальний вплив 10%
            
        return current_price * (Decimal('1') + impact) 