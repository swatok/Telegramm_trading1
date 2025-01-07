"""Risk calculator utilities"""

from decimal import Decimal
from typing import List, Dict, Optional
from models.position import Position
from models.portfolio import Portfolio

class RiskCalculator:
    """Клас для розрахунку ризиків"""
    
    @staticmethod
    def calculate_position_risk(
        position: Position,
        portfolio_value: Decimal
    ) -> Decimal:
        """Розрахунок ризику позиції відносно портфеля"""
        if portfolio_value == 0:
            return Decimal('0')
            
        potential_loss = position.current_value - (
            position.amount * position.stop_loss_level
            if position.stop_loss_level
            else position.current_value
        )
        
        return (potential_loss / portfolio_value) * Decimal('100')
    
    @staticmethod
    def calculate_portfolio_risk(portfolio: Portfolio) -> Decimal:
        """Розрахунок загального ризику портфеля"""
        if portfolio.total_value == 0:
            return Decimal('0')
            
        total_risk = sum(
            RiskCalculator.calculate_position_risk(pos, portfolio.total_value)
            for pos in portfolio.positions.values()
        )
        
        return total_risk
    
    @staticmethod
    def calculate_value_at_risk(
        returns: List[Decimal],
        confidence_level: Decimal = Decimal('0.95')
    ) -> Decimal:
        """Розрахунок Value at Risk"""
        if not returns:
            return Decimal('0')
            
        # Сортуємо прибутковості за зростанням
        sorted_returns = sorted(returns)
        
        # Визначаємо індекс для заданого рівня довіри
        index = int(len(returns) * (1 - confidence_level))
        
        # Повертаємо VaR як абсолютне значення
        return abs(sorted_returns[index])
    
    @staticmethod
    def calculate_expected_shortfall(
        returns: List[Decimal],
        confidence_level: Decimal = Decimal('0.95'
    )) -> Decimal:
        """Розрахунок Expected Shortfall (CVaR)"""
        if not returns:
            return Decimal('0')
            
        # Сортуємо прибутковості за зростанням
        sorted_returns = sorted(returns)
        
        # Визначаємо індекс для заданого рівня довіри
        index = int(len(returns) * (1 - confidence_level))
        
        # Розраховуємо середнє значення хвоста розподілу
        tail_returns = sorted_returns[:index]
        if not tail_returns:
            return Decimal('0')
            
        return abs(sum(tail_returns) / Decimal(len(tail_returns)))
    
    @staticmethod
    def calculate_position_size(
        portfolio_value: Decimal,
        risk_per_trade: Decimal,
        stop_loss_pct: Decimal
    ) -> Decimal:
        """Розрахунок розміру позиції на основі ризику"""
        if stop_loss_pct == 0:
            return Decimal('0')
            
        risk_amount = portfolio_value * (risk_per_trade / Decimal('100'))
        position_size = risk_amount / (stop_loss_pct / Decimal('100'))
        
        return position_size
    
    @staticmethod
    def calculate_kelly_criterion(
        win_rate: Decimal,
        win_loss_ratio: Decimal
    ) -> Decimal:
        """Розрахунок критерію Келлі"""
        win_rate = win_rate / Decimal('100')  # Конвертуємо з відсотків
        
        if win_loss_ratio <= 0:
            return Decimal('0')
            
        kelly = win_rate - ((1 - win_rate) / win_loss_ratio)
        
        # Обмежуємо результат від 0 до 1
        return max(min(kelly, Decimal('1')), Decimal('0'))
    
    @staticmethod
    def calculate_risk_adjusted_return(
        return_value: Decimal,
        risk_value: Decimal
    ) -> Decimal:
        """Розрахунок прибутковості з урахуванням ризику"""
        if risk_value == 0:
            return Decimal('0')
            
        return return_value / risk_value
    
    @staticmethod
    def calculate_max_position_size(
        portfolio_value: Decimal,
        max_position_pct: Decimal = Decimal('20')
    ) -> Decimal:
        """Розрахунок максимального розміру позиції"""
        return portfolio_value * (max_position_pct / Decimal('100'))
    
    @staticmethod
    def calculate_risk_of_ruin(
        win_rate: Decimal,
        risk_per_trade: Decimal,
        trades: int = 100
    ) -> Decimal:
        """Розрахунок ймовірності втрати всього капіталу"""
        win_rate = win_rate / Decimal('100')  # Конвертуємо з відсотків
        risk_per_trade = risk_per_trade / Decimal('100')
        
        if win_rate >= 1 or win_rate <= 0 or risk_per_trade >= 1:
            return Decimal('1')
            
        # Спрощена формула для ймовірності розорення
        q = Decimal('1') - win_rate
        r = win_rate / q
        
        if r == 1:
            return Decimal('1')
            
        return (((1 - r) / (1 + r)) ** trades) * Decimal('100')
    
    @staticmethod
    def calculate_risk_reward_zones(
        entry_price: Decimal,
        stop_loss: Decimal,
        take_profit: Decimal
    ) -> Dict[str, Decimal]:
        """Розрахунок зон ризику та прибутку"""
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        
        return {
            'risk_zone_start': min(entry_price, stop_loss),
            'risk_zone_end': max(entry_price, stop_loss),
            'reward_zone_start': min(entry_price, take_profit),
            'reward_zone_end': max(entry_price, take_profit),
            'risk_reward_ratio': reward / risk if risk != 0 else Decimal('0')
        } 