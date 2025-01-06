"""Менеджер позицій"""

from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger

from database import PositionRepository, TradeRepository
from model.position import Position

class PositionManager:
    """Клас для управління торговими позиціями"""
    
    def __init__(self, position_repo: PositionRepository, trade_repo: TradeRepository):
        """
        Ініціалізація менеджера позицій
        
        Args:
            position_repo: Репозиторій позицій
            trade_repo: Репозиторій торгів
        """
        self.position_repo = position_repo
        self.trade_repo = trade_repo
        self._active_positions: Dict[str, Position] = {}
        
    async def create_position(
        self,
        token_address: str,
        entry_price: Decimal,
        amount: Decimal,
        take_profit_levels: Optional[List[Dict[str, Decimal]]] = None,
        stop_loss_level: Optional[Decimal] = None
    ) -> Optional[Position]:
        """
        Створення нової позиції
        
        Args:
            token_address: Адреса токену
            entry_price: Ціна входу
            amount: Кількість
            take_profit_levels: Рівні take-profit
            stop_loss_level: Рівень stop-loss
            
        Returns:
            Створена позиція або None
        """
        try:
            # Створюємо об'єкт позиції
            position = Position(
                token_address=token_address,
                initial_amount=amount,
                entry_price=entry_price
            )
            
            if take_profit_levels:
                position.take_profit_levels = take_profit_levels
            if stop_loss_level is not None:
                position.stop_loss_level = stop_loss_level
                
            # Зберігаємо в БД
            position_data = position.to_dict()
            saved_position = await self.position_repo.add_position(position_data)
            
            if not saved_position:
                logger.error("Не вдалося зберегти позицію в БД")
                return None
                
            # Зберігаємо в пам'яті
            self._active_positions[token_address] = position
            
            logger.info(f"Створено нову позицію: {position}")
            return position
            
        except Exception as e:
            logger.error(f"Помилка створення позиції: {e}")
            return None
            
    async def close_position(
        self,
        token_address: str,
        close_price: Decimal,
        reason: str
    ) -> Optional[Position]:
        """
        Закриття позиції
        
        Args:
            token_address: Адреса токену
            close_price: Ціна закриття
            reason: Причина закриття
            
        Returns:
            Закрита позиція або None
        """
        try:
            position = self._active_positions.get(token_address)
            if not position:
                logger.error(f"Позицію {token_address} не знайдено")
                return None
                
            # Закриваємо позицію
            position.close_position(close_price, reason)
            
            # Оновлюємо в БД
            position_data = position.to_dict()
            updated_position = await self.position_repo.update_position(
                token_address, 
                position_data
            )
            
            if not updated_position:
                logger.error(f"Не вдалося оновити позицію {token_address} в БД")
                return None
                
            # Видаляємо з активних
            self._active_positions.pop(token_address)
            
            logger.info(f"Закрито позицію: {position}")
            return position
            
        except Exception as e:
            logger.error(f"Помилка закриття позиції: {e}")
            return None
            
    async def update_position_price(
        self,
        token_address: str,
        current_price: Decimal
    ) -> Optional[Position]:
        """
        Оновлення ціни позиції
        
        Args:
            token_address: Адреса токену
            current_price: Поточна ціна
            
        Returns:
            Оновлена позиція або None
        """
        try:
            position = self._active_positions.get(token_address)
            if not position:
                return None
                
            # Оновлюємо ціну
            position.update_price(current_price)
            
            # Перевіряємо take-profit
            tp_hit = position.check_take_profit()
            if tp_hit:
                logger.info(
                    f"Take-profit {tp_hit['level']}% досягнуто для {token_address}"
                )
                
            # Перевіряємо stop-loss
            if position.check_stop_loss():
                logger.info(f"Stop-loss досягнуто для {token_address}")
                await self.close_position(
                    token_address,
                    current_price,
                    "stop_loss"
                )
                
            return position
            
        except Exception as e:
            logger.error(f"Помилка оновлення ціни позиції: {e}")
            return None
            
    def get_position(self, token_address: str) -> Optional[Position]:
        """
        Отримання позиції за адресою токену
        
        Args:
            token_address: Адреса токену
            
        Returns:
            Позиція або None
        """
        return self._active_positions.get(token_address)
        
    def get_active_positions(self) -> List[Position]:
        """
        Отримання всіх активних позицій
        
        Returns:
            Список активних позицій
        """
        return list(self._active_positions.values())
        
    async def load_positions_from_db(self) -> None:
        """Завантаження активних позицій з БД"""
        try:
            positions_data = await self.position_repo.get_active_positions()
            for position_data in positions_data:
                position = Position(
                    token_address=position_data["token_address"],
                    initial_amount=Decimal(position_data["initial_amount"]),
                    entry_price=Decimal(position_data["entry_price"]),
                    timestamp=datetime.fromisoformat(position_data["timestamp"])
                )
                self._active_positions[position.token_address] = position
                
        except Exception as e:
            logger.error(f"Помилка завантаження позицій з БД: {e}")
