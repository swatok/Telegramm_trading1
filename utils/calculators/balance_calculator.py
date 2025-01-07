"""Balance calculator utilities"""

from decimal import Decimal
from typing import List, Dict
from models.position import Position
from models.portfolio import Portfolio

class BalanceCalculator:
    """Клас для розрахунків балансу та метрик портфеля"""
    
    @staticmethod
    def calculate_total_balance(positions: List[Position]) -> Decimal:
        """Розрахунок загального балансу по всіх позиціях"""
        return sum(position.current_value for position in positions)
    
    @staticmethod
    def calculate_total_pnl(positions: List[Position]) -> Decimal:
        """Розрахунок загального P&L по всіх позиціях"""
        return sum(position.pnl_value for position in positions)
    
    @staticmethod
    def calculate_position_weights(portfolio: Portfolio) -> Dict[str, Decimal]:
        """Розрахунок ваги кожної позиції в портфелі"""
        weights = {}
        total_value = portfolio.total_value
        
        if total_value == 0:
            return {pos.token_address: Decimal('0') for pos in portfolio.positions.values()}
            
        for token_address, position in portfolio.positions.items():
            weights[token_address] = (position.current_value / total_value) * Decimal('100')
            
        return weights
    
    @staticmethod
    def calculate_drawdown(portfolio: Portfolio) -> Decimal:
        """Розрахунок поточної просадки портфеля"""
        total_entry_value = sum(pos.entry_value for pos in portfolio.positions.values())
        current_value = portfolio.total_value
        
        if total_entry_value == 0:
            return Decimal('0')
            
        return ((total_entry_value - current_value) / total_entry_value) * Decimal('100')
    
    @staticmethod
    def calculate_position_exposure(position: Position, portfolio_value: Decimal) -> Decimal:
        """Розрахунок експозиції позиції відносно всього портфеля"""
        if portfolio_value == 0:
            return Decimal('0')
            
        return (position.current_value / portfolio_value) * Decimal('100')
    
    @staticmethod
    def calculate_required_adjustment(
        current_weight: Decimal,
        target_weight: Decimal,
        portfolio_value: Decimal
    ) -> Decimal:
        """Розрахунок необхідного коригування для досягнення цільової ваги"""
        return ((target_weight - current_weight) / Decimal('100')) * portfolio_value
    
    @staticmethod
    def estimate_rebalance_costs(
        adjustments: Dict[str, Decimal],
        fee_rate: Decimal
    ) -> Decimal:
        """Оцінка витрат на ребалансування"""
        total_adjustment_value = sum(abs(value) for value in adjustments.values())
        return total_adjustment_value * fee_rate
    
    @staticmethod
    def calculate_portfolio_diversity(weights: Dict[str, Decimal]) -> Decimal:
        """Розрахунок різноманітності портфеля (0-100)"""
        if not weights:
            return Decimal('0')
            
        # Використовуємо формулу індексу Херфіндаля-Хіршмана
        hhi = sum((weight / Decimal('100')) ** 2 for weight in weights.values())
        # Нормалізуємо до 0-100
        return (Decimal('1') - hhi) * Decimal('100') 