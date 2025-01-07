"""Slippage calculator utilities"""

from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class SlippageCalculator:
    """Калькулятор для розрахунків проковзування"""
    
    def __init__(self):
        self.historical_slippage: Dict[str, List[Dict]] = {}  # token -> [{timestamp, slippage}]
    
    def calculate_price_impact(self,
                             amount: Decimal,
                             liquidity: Decimal) -> Decimal:
        """Розрахунок впливу розміру ордеру на ціну"""
        return (amount / liquidity) * Decimal('100')
    
    def estimate_slippage(self,
                         token_address: str,
                         amount: Decimal,
                         liquidity: Decimal,
                         volatility: Optional[Decimal] = None) -> Decimal:
        """Оцінка очікуваного проковзування"""
        # Базове проковзування на основі розміру ордеру
        base_slippage = self.calculate_price_impact(amount, liquidity)
        
        # Додатковий коефіцієнт на основі волатильності
        volatility_multiplier = Decimal('1.0')
        if volatility:
            if volatility > Decimal('0.5'):  # Висока волатильність
                volatility_multiplier = Decimal('2.0')
            elif volatility > Decimal('0.2'):  # Середня волатильність
                volatility_multiplier = Decimal('1.5')
        
        # Історичний коефіцієнт
        historical_multiplier = self._get_historical_multiplier(token_address)
        
        final_slippage = base_slippage * volatility_multiplier * historical_multiplier
        return min(final_slippage, Decimal('10.0'))  # Максимум 10%
    
    def add_slippage_data(self,
                         token_address: str,
                         actual_slippage: Decimal) -> None:
        """Додавання даних про фактичне проковзування"""
        if token_address not in self.historical_slippage:
            self.historical_slippage[token_address] = []
            
        self.historical_slippage[token_address].append({
            'timestamp': datetime.now(),
            'slippage': actual_slippage
        })
        
        # Очищення старих даних
        self._cleanup_historical_data(token_address)
    
    def _cleanup_historical_data(self, token_address: str) -> None:
        """Очищення старих даних про проковзування"""
        if token_address not in self.historical_slippage:
            return
            
        cutoff = datetime.now() - timedelta(hours=24)
        self.historical_slippage[token_address] = [
            data for data in self.historical_slippage[token_address]
            if data['timestamp'] > cutoff
        ]
    
    def _get_historical_multiplier(self, token_address: str) -> Decimal:
        """Отримання історичного множника на основі попередніх даних"""
        if token_address not in self.historical_slippage:
            return Decimal('1.0')
            
        recent_data = [
            data for data in self.historical_slippage[token_address]
            if data['timestamp'] > datetime.now() - timedelta(hours=1)
        ]
        
        if not recent_data:
            return Decimal('1.0')
            
        avg_slippage = sum(d['slippage'] for d in recent_data) / len(recent_data)
        if avg_slippage > Decimal('5.0'):
            return Decimal('1.5')  # Високе історичне проковзування
        elif avg_slippage > Decimal('2.0'):
            return Decimal('1.2')  # Середнє історичне проковзування
        return Decimal('1.0')
    
    def get_optimal_order_size(self,
                             token_address: str,
                             liquidity: Decimal,
                             max_slippage: Decimal) -> Decimal:
        """Розрахунок оптимального розміру ордеру для заданого максимального проковзування"""
        historical_multiplier = self._get_historical_multiplier(token_address)
        adjusted_max_slippage = max_slippage / historical_multiplier
        
        # Зворотній розрахунок розміру ордеру
        optimal_size = (adjusted_max_slippage * liquidity) / Decimal('100')
        return optimal_size
    
    def calculate_effective_price(self,
                                base_price: Decimal,
                                slippage: Decimal,
                                side: str = 'buy') -> Decimal:
        """Розрахунок ефективної ціни з урахуванням проковзування"""
        slippage_decimal = slippage / Decimal('100')
        if side.lower() == 'buy':
            return base_price * (Decimal('1') + slippage_decimal)
        return base_price * (Decimal('1') - slippage_decimal) 