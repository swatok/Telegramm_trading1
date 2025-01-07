"""Position manager interface"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from decimal import Decimal
from datetime import datetime

from models.position import Position

class IPositionManager(ABC):
    """Інтерфейс для управління позиціями"""
    
    @abstractmethod
    async def create_position(
        self,
        token_address: str,
        amount: Decimal,
        entry_price: Decimal,
        current_price: Decimal,
        take_profit_levels: Optional[List[Decimal]] = None,
        stop_loss_level: Optional[Decimal] = None
    ) -> Optional[Position]:
        """Створення нової позиції"""
        pass
    
    @abstractmethod
    async def get_position(
        self,
        token_address: str
    ) -> Optional[Position]:
        """Отримання позиції за адресою токена"""
        pass
    
    @abstractmethod
    async def update_position(
        self,
        position: Position
    ) -> bool:
        """Оновлення позиції"""
        pass
    
    @abstractmethod
    async def delete_position(
        self,
        token_address: str
    ) -> bool:
        """Видалення позиції"""
        pass
    
    @abstractmethod
    async def get_all_positions(self) -> List[Position]:
        """Отримання всіх позицій"""
        pass
    
    @abstractmethod
    async def update_price(
        self,
        token_address: str,
        new_price: Decimal
    ) -> bool:
        """Оновлення ціни позиції"""
        pass
    
    @abstractmethod
    async def add_take_profit(
        self,
        token_address: str,
        level: Decimal
    ) -> bool:
        """Додавання рівня take profit"""
        pass
    
    @abstractmethod
    async def remove_take_profit(
        self,
        token_address: str,
        level: Decimal
    ) -> bool:
        """Видалення рівня take profit"""
        pass
    
    @abstractmethod
    async def set_stop_loss(
        self,
        token_address: str,
        level: Decimal
    ) -> bool:
        """Встановлення рівня stop loss"""
        pass
    
    @abstractmethod
    async def remove_stop_loss(
        self,
        token_address: str
    ) -> bool:
        """Видалення рівня stop loss"""
        pass
    
    @abstractmethod
    async def check_take_profit_hits(
        self,
        token_address: str
    ) -> List[Decimal]:
        """Перевірка досягнення рівнів take profit"""
        pass
    
    @abstractmethod
    async def check_stop_loss_hit(
        self,
        token_address: str
    ) -> bool:
        """Перевірка досягнення рівня stop loss"""
        pass
    
    @abstractmethod
    async def get_position_history(
        self,
        token_address: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[tuple[datetime, Decimal]]:
        """Отримання історії цін позиції"""
        pass
    
    @abstractmethod
    async def calculate_pnl(
        self,
        token_address: str
    ) -> Optional[Decimal]:
        """Розрахунок P&L позиції"""
        pass
    
    @abstractmethod
    async def calculate_unrealized_pnl(
        self,
        token_address: str
    ) -> Optional[Decimal]:
        """Розрахунок нереалізованого P&L"""
        pass
    
    @abstractmethod
    async def adjust_position_size(
        self,
        token_address: str,
        new_amount: Decimal
    ) -> bool:
        """Коригування розміру позиції"""
        pass
    
    @abstractmethod
    async def get_active_positions(self) -> List[Position]:
        """Отримання активних позицій"""
        pass
    
    @abstractmethod
    async def get_closed_positions(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Position]:
        """Отримання закритих позицій"""
        pass 