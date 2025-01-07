"""Calculator interfaces"""

from abc import ABC, abstractmethod
from typing import Dict, Optional
from decimal import Decimal
from datetime import datetime

class IGasCalculator(ABC):
    """Інтерфейс для розрахунків газу"""
    
    @abstractmethod
    def estimate_gas_price(self,
                          network_load: float,
                          priority: str = 'normal') -> Decimal:
        """Оцінка ціни газу"""
        pass
        
    @abstractmethod
    def estimate_gas_limit(self,
                          operation_type: str,
                          token_address: str,
                          amount: Decimal,
                          historical_data: Optional[Dict] = None) -> int:
        """Оцінка ліміту газу"""
        pass
        
    @abstractmethod
    def calculate_total_gas_cost(self,
                               gas_price: Decimal,
                               gas_limit: int) -> Decimal:
        """Розрахунок повної вартості газу"""
        pass

class ISlippageCalculator(ABC):
    """Інтерфейс для розрахунків проковзування"""
    
    @abstractmethod
    def calculate_price_impact(self,
                             amount: Decimal,
                             liquidity: Decimal) -> Decimal:
        """Розрахунок впливу на ціну"""
        pass
        
    @abstractmethod
    def estimate_slippage(self,
                         token_address: str,
                         amount: Decimal,
                         liquidity: Decimal,
                         volatility: Optional[Decimal] = None) -> Decimal:
        """Оцінка проковзування"""
        pass
        
    @abstractmethod
    def get_optimal_order_size(self,
                             token_address: str,
                             liquidity: Decimal,
                             max_slippage: Decimal) -> Decimal:
        """Розрахунок оптимального розміру ордеру"""
        pass 