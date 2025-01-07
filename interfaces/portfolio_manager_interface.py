"""Portfolio manager interface"""

from abc import ABC, abstractmethod
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

from models.portfolio import Portfolio
from models.position import Position

class IPortfolioManager(ABC):
    """Інтерфейс для управління портфелем"""
    
    @abstractmethod
    async def create_portfolio(self, wallet_address: str) -> Portfolio:
        """Створення нового портфеля"""
        pass
    
    @abstractmethod
    async def get_portfolio(self, wallet_address: str) -> Optional[Portfolio]:
        """Отримання портфеля за адресою гаманця"""
        pass
    
    @abstractmethod
    async def update_portfolio(self, portfolio: Portfolio) -> bool:
        """Оновлення портфеля"""
        pass
    
    @abstractmethod
    async def delete_portfolio(self, wallet_address: str) -> bool:
        """Видалення портфеля"""
        pass
    
    @abstractmethod
    async def add_position(
        self,
        wallet_address: str,
        token_address: str,
        amount: Decimal,
        entry_price: Decimal
    ) -> Optional[Position]:
        """Додавання нової позиції до портфеля"""
        pass
    
    @abstractmethod
    async def remove_position(
        self,
        wallet_address: str,
        token_address: str
    ) -> bool:
        """Видалення позиції з портфеля"""
        pass
    
    @abstractmethod
    async def update_position(
        self,
        wallet_address: str,
        position: Position
    ) -> bool:
        """Оновлення позиції в портфелі"""
        pass
    
    @abstractmethod
    async def get_position(
        self,
        wallet_address: str,
        token_address: str
    ) -> Optional[Position]:
        """Отримання позиції з портфеля"""
        pass
    
    @abstractmethod
    async def get_all_positions(
        self,
        wallet_address: str
    ) -> List[Position]:
        """Отримання всіх позицій портфеля"""
        pass
    
    @abstractmethod
    async def update_prices(
        self,
        wallet_address: str,
        price_updates: dict[str, Decimal]
    ) -> bool:
        """Оновлення цін для позицій"""
        pass
    
    @abstractmethod
    async def calculate_total_value(
        self,
        wallet_address: str
    ) -> Optional[Decimal]:
        """Розрахунок загальної вартості портфеля"""
        pass
    
    @abstractmethod
    async def calculate_pnl(
        self,
        wallet_address: str
    ) -> Optional[Decimal]:
        """Розрахунок загального P&L портфеля"""
        pass
    
    @abstractmethod
    async def get_portfolio_history(
        self,
        wallet_address: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[tuple[datetime, Decimal]]:
        """Отримання історії вартості портфеля"""
        pass
    
    @abstractmethod
    async def get_position_weights(
        self,
        wallet_address: str
    ) -> dict[str, Decimal]:
        """Отримання ваги кожної позиції в портфелі"""
        pass
    
    @abstractmethod
    async def rebalance_portfolio(
        self,
        wallet_address: str,
        target_weights: dict[str, Decimal]
    ) -> bool:
        """Ребалансування портфеля до цільових ваг"""
        pass 