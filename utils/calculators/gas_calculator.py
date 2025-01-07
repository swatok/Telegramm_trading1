"""Gas calculator utilities"""

from decimal import Decimal
from typing import Dict, Optional
from datetime import datetime, timedelta

class GasCalculator:
    """Калькулятор для розрахунків пов'язаних з газом"""
    
    def __init__(self):
        self.historical_prices: Dict[datetime, Decimal] = {}
        self.base_gas_units = {
            'swap': 150000,
            'approve': 50000,
            'transfer': 35000
        }
    
    def estimate_gas_price(self,
                          network_load: float,
                          priority: str = 'normal') -> Decimal:
        """Оцінка ціни газу на основі завантаженості мережі"""
        base_price = Decimal('0.000001')  # Базова ціна в SOL
        
        # Коефіцієнти для різних пріоритетів
        priority_multipliers = {
            'low': Decimal('0.8'),
            'normal': Decimal('1.0'),
            'high': Decimal('1.5'),
            'urgent': Decimal('2.0')
        }
        
        # Коефіцієнт завантаженості мережі
        load_multiplier = Decimal(str(1 + network_load))
        
        return base_price * priority_multipliers.get(priority, Decimal('1.0')) * load_multiplier
    
    def estimate_gas_limit(self,
                          operation_type: str,
                          token_address: str,
                          amount: Decimal,
                          historical_data: Optional[Dict] = None) -> int:
        """Оцінка ліміту газу для операції"""
        base_limit = self.base_gas_units.get(operation_type, 100000)
        
        # Множник на основі розміру транзакції
        size_multiplier = 1.0
        if amount > Decimal('10.0'):
            size_multiplier = 1.2
        elif amount > Decimal('100.0'):
            size_multiplier = 1.5
        
        # Множник на основі історичних даних
        history_multiplier = 1.0
        if historical_data and token_address in historical_data:
            avg_gas = historical_data[token_address].get('average_gas', base_limit)
            history_multiplier = avg_gas / base_limit
        
        final_limit = int(base_limit * size_multiplier * history_multiplier)
        return min(final_limit, 300000)  # Максимальний ліміт
    
    def calculate_total_gas_cost(self,
                               gas_price: Decimal,
                               gas_limit: int) -> Decimal:
        """Розрахунок повної вартості газу"""
        return gas_price * Decimal(str(gas_limit))
    
    def add_historical_price(self,
                           timestamp: datetime,
                           price: Decimal) -> None:
        """Додавання історичної ціни газу"""
        self.historical_prices[timestamp] = price
        
        # Видалення старих даних (старше 24 годин)
        cutoff = datetime.now() - timedelta(hours=24)
        self.historical_prices = {
            ts: price for ts, price in self.historical_prices.items()
            if ts > cutoff
        }
    
    def get_average_price(self,
                         period: timedelta = timedelta(minutes=5)) -> Optional[Decimal]:
        """Отримання середньої ціни газу за період"""
        if not self.historical_prices:
            return None
            
        cutoff = datetime.now() - period
        recent_prices = [
            price for ts, price in self.historical_prices.items()
            if ts > cutoff
        ]
        
        if not recent_prices:
            return None
            
        return sum(recent_prices) / Decimal(str(len(recent_prices)))
    
    def estimate_optimal_gas_price(self,
                                 target_confirmation_time: int = 30) -> Decimal:
        """Оцінка оптимальної ціни газу для цільового часу підтвердження"""
        avg_price = self.get_average_price()
        if not avg_price:
            return Decimal('0.000001')  # Дефолтна ціна
            
        # Коефіцієнти для різних часів підтвердження
        if target_confirmation_time <= 15:
            return avg_price * Decimal('1.5')
        elif target_confirmation_time <= 30:
            return avg_price * Decimal('1.2')
        elif target_confirmation_time <= 60:
            return avg_price * Decimal('1.0')
        else:
            return avg_price * Decimal('0.8') 