"""Position service implementation"""

from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime

from interfaces.position_interface import IPositionService
from implementations.api.market_api import MarketAPI
from model.position import Position

class PositionService(IPositionService):
    """Сервіс для управління позиціями"""
    
    def __init__(self, market_api: MarketAPI):
        self._market_api = market_api
        self._positions: Dict[str, Position] = {}
        
    async def open_position(self,
                          token_address: str,
                          amount: Decimal,
                          entry_price: Decimal,
                          side: str) -> Position:
        """Відкриття нової позиції"""
        position = Position(
            token_address=token_address,
            amount=amount,
            entry_price=entry_price,
            side=side,
            timestamp=datetime.now()
        )
        
        self._positions[token_address] = position
        return position
        
    async def close_position(self,
                           token_address: str,
                           exit_price: Decimal) -> Position:
        """Закриття позиції"""
        if token_address not in self._positions:
            raise ValueError("Position not found")
            
        position = self._positions[token_address]
        position.close(exit_price)
        
        del self._positions[token_address]
        return position
        
    async def update_position(self,
                            token_address: str,
                            amount: Optional[Decimal] = None,
                            price: Optional[Decimal] = None) -> Position:
        """Оновлення позиції"""
        if token_address not in self._positions:
            raise ValueError("Position not found")
            
        position = self._positions[token_address]
        
        if amount is not None:
            position.update_amount(amount)
            
        if price is not None:
            position.update_price(price)
            
        return position
        
    async def get_position(self, token_address: str) -> Optional[Position]:
        """Отримання позиції"""
        return self._positions.get(token_address)
        
    async def get_positions(self) -> List[Position]:
        """Отримання всіх позицій"""
        return list(self._positions.values())
        
    async def get_position_pnl(self, token_address: str) -> Dict:
        """Отримання P&L позиції"""
        position = await self.get_position(token_address)
        if not position:
            return None
            
        current_price = await self._market_api.get_token_price(token_address)
        unrealized_pnl = position.calculate_pnl(current_price)
        
        return {
            'unrealized_pnl': unrealized_pnl,
            'pnl_percentage': (unrealized_pnl / (position.entry_price * position.amount)) * 100
        }
        
    async def get_total_value(self) -> Decimal:
        """Отримання загальної вартості позицій"""
        total = Decimal('0')
        
        for position in self._positions.values():
            current_price = await self._market_api.get_token_price(position.token_address)
            total += position.amount * current_price
            
        return total 