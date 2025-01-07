"""Performance calculator utilities"""

from decimal import Decimal
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from models.performance import PerformanceMetrics
from models.position import Position

class PerformanceCalculator:
    """Клас для розрахунку метрик продуктивності"""
    
    @staticmethod
    def calculate_success_rate(
        successful_trades: int,
        total_trades: int
    ) -> Decimal:
        """Розрахунок відсотка успішних угод"""
        if total_trades == 0:
            return Decimal('0')
        return Decimal(successful_trades) / Decimal(total_trades) * Decimal('100')
    
    @staticmethod
    def calculate_profit_factor(
        total_profit: Decimal,
        total_loss: Decimal
    ) -> Decimal:
        """Розрахунок фактору прибутковості"""
        if total_loss == 0:
            return Decimal('0') if total_profit == 0 else Decimal('inf')
        return total_profit / abs(total_loss)
    
    @staticmethod
    def calculate_average_profit(
        total_profit: Decimal,
        successful_trades: int
    ) -> Decimal:
        """Розрахунок середнього прибутку"""
        if successful_trades == 0:
            return Decimal('0')
        return total_profit / Decimal(successful_trades)
    
    @staticmethod
    def calculate_average_loss(
        total_loss: Decimal,
        failed_trades: int
    ) -> Decimal:
        """Розрахунок середнього збитку"""
        if failed_trades == 0:
            return Decimal('0')
        return total_loss / Decimal(failed_trades)
    
    @staticmethod
    def calculate_risk_reward_ratio(
        avg_profit: Decimal,
        avg_loss: Decimal
    ) -> Decimal:
        """Розрахунок співвідношення ризик/прибуток"""
        if avg_loss == 0:
            return Decimal('0')
        return avg_profit / avg_loss
    
    @staticmethod
    def calculate_expectancy(
        success_rate: Decimal,
        avg_profit: Decimal,
        avg_loss: Decimal
    ) -> Decimal:
        """Розрахунок математичного очікування"""
        win_rate = success_rate / Decimal('100')
        loss_rate = Decimal('1') - win_rate
        return (win_rate * avg_profit) - (loss_rate * avg_loss)
    
    @staticmethod
    def calculate_sharpe_ratio(
        returns: List[Decimal],
        risk_free_rate: Decimal = Decimal('0.02')
    ) -> Decimal:
        """Розрахунок коефіцієнта Шарпа"""
        if not returns:
            return Decimal('0')
            
        # Розрахунок середньої прибутковості
        avg_return = sum(returns) / Decimal(len(returns))
        
        # Розрахунок стандартного відхилення
        variance = sum((r - avg_return) ** 2 for r in returns) / Decimal(len(returns))
        std_dev = variance.sqrt()
        
        if std_dev == 0:
            return Decimal('0')
            
        # Розрахунок коефіцієнта Шарпа
        return (avg_return - risk_free_rate) / std_dev
    
    @staticmethod
    def calculate_sortino_ratio(
        returns: List[Decimal],
        risk_free_rate: Decimal = Decimal('0.02')
    ) -> Decimal:
        """Розрахунок коефіцієнта Сортіно"""
        if not returns:
            return Decimal('0')
            
        # Розрахунок середньої прибутковості
        avg_return = sum(returns) / Decimal(len(returns))
        
        # Розрахунок негативного стандартного відхилення
        negative_returns = [r for r in returns if r < 0]
        if not negative_returns:
            return Decimal('0')
            
        downside_variance = sum((r - avg_return) ** 2 for r in negative_returns) / Decimal(len(negative_returns))
        downside_std = downside_variance.sqrt()
        
        if downside_std == 0:
            return Decimal('0')
            
        # Розрахунок коефіцієнта Сортіно
        return (avg_return - risk_free_rate) / downside_std
    
    @staticmethod
    def calculate_max_drawdown(
        equity_curve: List[Decimal]
    ) -> Decimal:
        """Розрахунок максимальної просадки"""
        if not equity_curve:
            return Decimal('0')
            
        peak = equity_curve[0]
        max_dd = Decimal('0')
        
        for value in equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak * Decimal('100')
            max_dd = min(max_dd, dd)
            
        return abs(max_dd)
    
    @staticmethod
    def calculate_recovery_factor(
        total_return: Decimal,
        max_drawdown: Decimal,
        period_days: int
    ) -> Decimal:
        """Розрахунок фактору відновлення"""
        if max_drawdown == 0 or period_days == 0:
            return Decimal('0')
            
        return (total_return / max_drawdown) / Decimal(period_days)
    
    @staticmethod
    def calculate_calmar_ratio(
        annual_return: Decimal,
        max_drawdown: Decimal
    ) -> Decimal:
        """Розрахунок коефіцієнта Кальмара"""
        if max_drawdown == 0:
            return Decimal('0')
            
        return annual_return / max_drawdown
    
    @staticmethod
    def calculate_win_loss_ratio(
        successful_trades: int,
        failed_trades: int
    ) -> Decimal:
        """Розрахунок співвідношення виграшів до програшів"""
        if failed_trades == 0:
            return Decimal('0') if successful_trades == 0 else Decimal('inf')
        return Decimal(successful_trades) / Decimal(failed_trades)
    
    @staticmethod
    def calculate_average_trade_duration(
        total_duration: int,
        total_trades: int
    ) -> int:
        """Розрахунок середньої тривалості угоди в секундах"""
        if total_trades == 0:
            return 0
        return total_duration // total_trades
    
    @staticmethod
    def calculate_profit_per_day(
        total_profit: Decimal,
        period_days: int
    ) -> Decimal:
        """Розрахунок середнього прибутку за день"""
        if period_days == 0:
            return Decimal('0')
        return total_profit / Decimal(period_days)
    
    @staticmethod
    def calculate_trades_per_day(
        total_trades: int,
        period_days: int
    ) -> Decimal:
        """Розрахунок середньої кількості угод за день"""
        if period_days == 0:
            return Decimal('0')
        return Decimal(total_trades) / Decimal(period_days) 