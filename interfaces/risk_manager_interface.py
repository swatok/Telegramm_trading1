"""Risk manager interface"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from decimal import Decimal
from datetime import datetime

from models.portfolio import Portfolio
from models.position import Position

class IRiskManager(ABC):
    """Інтерфейс для управління ризиками"""
    
    @abstractmethod
    async def calculate_position_risk(
        self,
        position: Position,
        portfolio_value: Decimal
    ) -> Decimal:
        """Розрахунок ризику позиції"""
        pass
    
    @abstractmethod
    async def calculate_portfolio_risk(
        self,
        portfolio: Portfolio
    ) -> Decimal:
        """Розрахунок загального ризику портфеля"""
        pass
    
    @abstractmethod
    async def calculate_value_at_risk(
        self,
        portfolio: Portfolio,
        confidence_level: Decimal = Decimal('0.95'),
        time_horizon: int = 1
    ) -> Decimal:
        """Розрахунок Value at Risk"""
        pass
    
    @abstractmethod
    async def calculate_expected_shortfall(
        self,
        portfolio: Portfolio,
        confidence_level: Decimal = Decimal('0.95')
    ) -> Decimal:
        """Розрахунок Expected Shortfall (CVaR)"""
        pass
    
    @abstractmethod
    async def check_position_limits(
        self,
        portfolio: Portfolio,
        token_address: str,
        amount: Decimal,
        price: Decimal
    ) -> bool:
        """Перевірка лімітів позиції"""
        pass
    
    @abstractmethod
    async def check_portfolio_limits(
        self,
        portfolio: Portfolio
    ) -> Dict[str, bool]:
        """Перевірка лімітів портфеля"""
        pass
    
    @abstractmethod
    async def calculate_optimal_position_size(
        self,
        portfolio: Portfolio,
        token_address: str,
        risk_per_trade: Decimal,
        stop_loss_pct: Decimal
    ) -> Optional[Decimal]:
        """Розрахунок оптимального розміру позиції"""
        pass
    
    @abstractmethod
    async def calculate_kelly_criterion(
        self,
        win_rate: Decimal,
        win_loss_ratio: Decimal
    ) -> Decimal:
        """Розрахунок критерію Келлі"""
        pass
    
    @abstractmethod
    async def check_correlation_limits(
        self,
        portfolio: Portfolio,
        token_address: str
    ) -> bool:
        """Перевірка лімітів кореляції"""
        pass
    
    @abstractmethod
    async def calculate_risk_metrics(
        self,
        portfolio: Portfolio
    ) -> Dict[str, Decimal]:
        """Розрахунок метрик ризику"""
        pass
    
    @abstractmethod
    async def check_drawdown_limits(
        self,
        portfolio: Portfolio,
        max_drawdown: Decimal = Decimal('20')
    ) -> bool:
        """Перевірка лімітів просадки"""
        pass
    
    @abstractmethod
    async def calculate_risk_adjusted_returns(
        self,
        portfolio: Portfolio
    ) -> Dict[str, Decimal]:
        """Розрахунок прибутковості з урахуванням ризику"""
        pass
    
    @abstractmethod
    async def check_concentration_limits(
        self,
        portfolio: Portfolio,
        max_weight: Decimal = Decimal('20')
    ) -> Dict[str, bool]:
        """Перевірка лімітів концентрації"""
        pass
    
    @abstractmethod
    async def calculate_portfolio_beta(
        self,
        portfolio: Portfolio,
        market_returns: List[Decimal]
    ) -> Decimal:
        """Розрахунок бети портфеля"""
        pass
    
    @abstractmethod
    async def check_leverage_limits(
        self,
        portfolio: Portfolio,
        max_leverage: Decimal = Decimal('2')
    ) -> bool:
        """Перевірка лімітів кредитного плеча"""
        pass
    
    @abstractmethod
    async def calculate_risk_contribution(
        self,
        portfolio: Portfolio
    ) -> Dict[str, Decimal]:
        """Розрахунок внеску в ризик кожної позиції"""
        pass
    
    @abstractmethod
    async def get_risk_alerts(
        self,
        portfolio: Portfolio
    ) -> List[str]:
        """Отримання попереджень про ризики"""
        pass 