"""
Менеджер виконання торгових операцій
"""

import asyncio
from decimal import Decimal
from typing import Dict, Optional, List
from loguru import logger

from api.jupiter import JupiterAPI
from api.quicknode import QuicknodeAPI
from database import (
    PositionRepository,
    TradeRepository,
    TransactionRepository
)

from .blockchain_sync import BlockchainSync
from .position_manager import PositionManager
from .order_executor import OrderExecutor
from .price_calculator import PriceCalculator
from .risk_manager import RiskManager
from .trade_validator import TradeValidator

class TradeExecutionManager:
    """Менеджер виконання торгових операцій"""
    
    def __init__(
        self,
        jupiter_api: JupiterAPI,
        quicknode_api: QuicknodeAPI,
        position_repo: PositionRepository,
        trade_repo: TradeRepository,
        transaction_repo: TransactionRepository,
        wallet_address: str
    ):
        # Ініціалізуємо компоненти виконання
        self.blockchain_sync = BlockchainSync(quicknode_api)
        self.position_manager = PositionManager(position_repo, trade_repo)
        self.order_executor = OrderExecutor(jupiter_api, quicknode_api, transaction_repo)
        self.price_calculator = PriceCalculator(jupiter_api)
        self.risk_manager = RiskManager(jupiter_api, quicknode_api)
        self.trade_validator = TradeValidator(jupiter_api, quicknode_api)
        
        self._is_running = False
        self._tasks: List[asyncio.Task] = []
        
    async def initialize(self) -> bool:
        """Ініціалізація компонентів виконання"""
        try:
            await self.blockchain_sync.start()
            await self.position_manager.initialize()
            await self.order_executor.initialize()
            return True
        except Exception as e:
            logger.error(f"Помилка ініціалізації компонентів виконання: {e}")
            return False
            
    async def stop(self) -> bool:
        """Зупинка менеджера виконання"""
        try:
            self._is_running = False
            
            for task in self._tasks:
                task.cancel()
            await asyncio.gather(*self._tasks, return_exceptions=True)
            
            await self.blockchain_sync.stop()
            return True
        except Exception as e:
            logger.error(f"Помилка зупинки менеджера виконання: {e}")
            return False
            
    async def handle_price_update(self, price_update: Dict):
        """Обробка оновлення цін"""
        try:
            token_address = price_update['token_address']
            price = Decimal(price_update['price'])
            
            # Перевіряємо відкриті позиції
            positions = await self.position_manager.get_positions_by_token(token_address)
            for position in positions:
                await self._check_position_status(position, price)
                
        except Exception as e:
            logger.error(f"Помилка обробки оновлення цін: {e}")
            
    async def _check_position_status(self, position: Dict, current_price: Decimal):
        """Перевірка статусу позиції"""
        try:
            # Перевіряємо умови закриття
            if await self._should_close_position(position, current_price):
                await self._close_position(position, current_price)
                
            # Перевіряємо умови часткового закриття
            elif await self._should_partial_close(position, current_price):
                await self._partial_close_position(position, current_price)
                
        except Exception as e:
            logger.error(f"Помилка перевірки статусу позиції: {e}")
            
    async def _should_close_position(self, position: Dict, current_price: Decimal) -> bool:
        """Перевірка необхідності закриття позиції"""
        try:
            # Перевіряємо стоп-лосс
            if position['stop_loss'] and current_price <= Decimal(position['stop_loss']):
                return True
                
            # Перевіряємо тейк-профіт
            if position['take_profit'] and current_price >= Decimal(position['take_profit']):
                return True
                
            # Перевіряємо ризики
            risk_assessment = await self.risk_manager.assess_position_risk(position, current_price)
            if risk_assessment['should_close']:
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Помилка перевірки закриття позиції: {e}")
            return False
            
    async def _close_position(self, position: Dict, current_price: Decimal):
        """Закриття позиції"""
        try:
            # Валідація закриття
            if not await self.trade_validator.validate_close(position, current_price):
                logger.warning("Закриття позиції не пройшло валідацію")
                return
                
            # Розрахунок параметрів закриття
            close_params = await self.price_calculator.calculate_close_params(
                position,
                current_price
            )
            
            # Виконання закриття
            success = await self.order_executor.execute_close(
                position['id'],
                close_params
            )
            
            if success:
                await self.position_manager.mark_position_closed(
                    position['id'],
                    current_price
                )
                logger.info(f"Позиція {position['id']} успішно закрита")
                
        except Exception as e:
            logger.error(f"Помилка закриття позиції: {e}")
            
    async def _should_partial_close(self, position: Dict, current_price: Decimal) -> bool:
        """Перевірка необхідності часткового закриття"""
        try:
            # Перевіряємо проміжні цілі
            if position['partial_take_profits']:
                for target in position['partial_take_profits']:
                    if current_price >= Decimal(target['price']) and not target['executed']:
                        return True
                        
            return False
            
        except Exception as e:
            logger.error(f"Помилка перевірки часткового закриття: {e}")
            return False
            
    async def _partial_close_position(self, position: Dict, current_price: Decimal):
        """Часткове закриття позиції"""
        try:
            # Знаходимо відповідну ціль
            target = next(
                (t for t in position['partial_take_profits']
                if current_price >= Decimal(t['price']) and not t['executed']),
                None
            )
            
            if not target:
                return
                
            # Валідація часткового закриття
            if not await self.trade_validator.validate_partial_close(position, target):
                logger.warning("Часткове закриття не пройшло валідацію")
                return
                
            # Розрахунок параметрів
            close_params = await self.price_calculator.calculate_partial_close_params(
                position,
                target,
                current_price
            )
            
            # Виконання часткового закриття
            success = await self.order_executor.execute_partial_close(
                position['id'],
                close_params
            )
            
            if success:
                await self.position_manager.mark_partial_close_executed(
                    position['id'],
                    target['id']
                )
                logger.info(f"Часткове закриття позиції {position['id']} успішно виконано")
                
        except Exception as e:
            logger.error(f"Помилка часткового закриття позиції: {e}")
            
    async def check_health(self) -> Dict:
        """Перевірка стану менеджера"""
        try:
            return {
                'healthy': True,
                'details': {
                    'blockchain_sync': await self.blockchain_sync.check_health(),
                    'position_manager': await self.position_manager.check_health(),
                    'order_executor': await self.order_executor.check_health()
                }
            }
        except Exception as e:
            return {
                'healthy': False,
                'details': str(e)
            } 