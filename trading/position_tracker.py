"""
Модуль для відстеження торгових позицій.
"""

from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime

from .constants import TAKE_PROFIT_LEVELS, STOP_LOSS_LEVEL
from .price_monitor import PriceMonitor
from .position_manager import PositionManager
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class PositionTracker:
    """
    Клас для відстеження позицій.
    Відповідає за моніторинг цін та виконання take-profit/stop-loss стратегій.
    """

    def __init__(self, position_manager: PositionManager, price_monitor: PriceMonitor):
        """
        Ініціалізація трекера позицій.

        Args:
            position_manager: Менеджер позицій
            price_monitor: Монітор цін
        """
        self.position_manager = position_manager
        self.price_monitor = price_monitor

    async def track_positions(self):
        """Відстеження всіх активних позицій"""
        active_positions = self.position_manager.get_active_positions()
        
        for position in active_positions:
            price_data = await self.price_monitor.get_current_price(position.token_address)
            if not price_data:
                logger.warning(f"Не вдалося отримати ціну для {position.token_address}")
                continue
                
            current_price = Decimal(str(price_data['price']))
            await self.position_manager.update_position_price(
                position.token_address,
                current_price
            )

    async def create_tracked_position(
        self,
        token_address: str,
        entry_price: Decimal,
        amount: Decimal
    ) -> bool:
        """
        Створення нової позиції з відстеженням.

        Args:
            token_address: Адреса токену
            entry_price: Ціна входу
            amount: Кількість токенів

        Returns:
            True якщо позиція створена успішно
        """
        try:
            # Створюємо позицію з налаштованими рівнями
            position = await self.position_manager.create_position(
                token_address=token_address,
                entry_price=entry_price,
                amount=amount,
                take_profit_levels=TAKE_PROFIT_LEVELS,
                stop_loss_level=STOP_LOSS_LEVEL
            )
            
            if not position:
                logger.error("Не вдалося створити позицію")
                return False
                
            logger.info(f"Створено позицію з відстеженням: {position}")
            return True
            
        except Exception as e:
            logger.error(f"Помилка створення позиції з відстеженням: {e}")
            return False

    def get_position_stats(self, token_address: str) -> Optional[Dict]:
        """
        Отримання статистики по позиції.

        Args:
            token_address: Адреса токену

        Returns:
            Словник зі статистикою або None
        """
        position = self.position_manager.get_position(token_address)
        if not position:
            return None
            
        return position.to_dict() 