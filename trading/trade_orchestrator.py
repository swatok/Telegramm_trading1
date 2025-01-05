"""
Координатор торгових операцій
"""

import asyncio
from typing import List, Optional
from loguru import logger

from api.jupiter import JupiterAPI
from api.quicknode import QuicknodeAPI
from database import (
    PositionRepository,
    TradeRepository,
    TransactionRepository
)

from .session_manager import SessionManager
from .websocket_manager import WebSocketManager
from .wallet_balance_manager import WalletBalanceManager
from .wallet_account_manager import WalletAccountManager
from .trade_execution_manager import TradeExecutionManager
from .trade_analytics_manager import TradeAnalyticsManager

class TradeOrchestrator:
    """Координатор торгових операцій"""
    
    def __init__(
        self,
        jupiter_api: JupiterAPI,
        quicknode_api: QuicknodeAPI,
        position_repo: PositionRepository,
        trade_repo: TradeRepository,
        transaction_repo: TransactionRepository,
        wallet_address: str,
        send_log_callback=None
    ):
        self.send_log = send_log_callback
        
        # Базові компоненти
        self.session_manager = SessionManager()
        self.websocket_manager = WebSocketManager(jupiter_api, quicknode_api)
        
        # Менеджери гаманця
        self.wallet_balance_manager = WalletBalanceManager(
            quicknode_api,
            jupiter_api,
            wallet_address
        )
        self.wallet_account_manager = WalletAccountManager(
            quicknode_api,
            jupiter_api,
            wallet_address
        )
        
        # Спеціалізовані менеджери
        self.execution_manager = TradeExecutionManager(
            jupiter_api,
            quicknode_api,
            position_repo,
            trade_repo,
            transaction_repo,
            wallet_address
        )
        self.analytics_manager = TradeAnalyticsManager(
            position_repo,
            trade_repo,
            transaction_repo
        )
        
        self._is_running = False
        self._tasks: List[asyncio.Task] = []
        
    async def initialize(self) -> bool:
        """Ініціалізація всіх компонентів"""
        try:
            logger.info("Починаємо ініціалізацію компонентів...")
            
            # Ініціалізуємо базові компоненти
            await self.session_manager.start()
            await self.websocket_manager.connect()
            await self.wallet_balance_manager.update_balances()
            
            # Ініціалізуємо спеціалізовані менеджери
            await self.execution_manager.initialize()
            await self.analytics_manager.initialize()
            
            logger.info("Всі компоненти успішно ініціалізовано")
            return True
            
        except Exception as e:
            logger.error(f"Помилка ініціалізації компонентів: {e}")
            return False
            
    async def start(self) -> bool:
        """Запуск координатора"""
        try:
            if not await self.initialize():
                return False
                
            self._tasks = [
                asyncio.create_task(self._coordinate_trading()),
                asyncio.create_task(self._monitor_system_health())
            ]
            
            self._is_running = True
            logger.info("Координатор торгових операцій запущено")
            return True
            
        except Exception as e:
            logger.error(f"Помилка запуску координатора: {e}")
            return False
            
    async def stop(self) -> bool:
        """Зупинка координатора"""
        try:
            self._is_running = False
            
            for task in self._tasks:
                task.cancel()
            await asyncio.gather(*self._tasks, return_exceptions=True)
            
            await self.session_manager.stop()
            await self.websocket_manager.disconnect()
            await self.execution_manager.stop()
            await self.analytics_manager.stop()
            
            logger.info("Координатор торгових операцій зупинено")
            return True
            
        except Exception as e:
            logger.error(f"Помилка зупинки координатора: {e}")
            return False
            
    async def _coordinate_trading(self):
        """Координація торгових операцій"""
        while self._is_running:
            try:
                # Отримуємо оновлення цін
                price_update = await self.websocket_manager.get_price_update()
                if price_update:
                    # Передаємо дані виконавчому менеджеру
                    await self.execution_manager.handle_price_update(price_update)
                    # Оновлюємо аналітику
                    await self.analytics_manager.update_price_analytics(price_update)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Помилка координації торгівлі: {e}")
                await asyncio.sleep(1)
                
    async def _monitor_system_health(self):
        """Моніторинг здоров'я системи"""
        while self._is_running:
            try:
                # Перевіряємо стан компонентів
                components_status = {
                    'session': await self.session_manager.check_health(),
                    'websocket': await self.websocket_manager.check_health(),
                    'wallet': await self.wallet_balance_manager.check_health(),
                    'execution': await self.execution_manager.check_health(),
                    'analytics': await self.analytics_manager.check_health()
                }
                
                # Логуємо проблеми
                for component, status in components_status.items():
                    if not status['healthy']:
                        logger.warning(f"Проблема з компонентом {component}: {status['details']}")
                        
                await asyncio.sleep(60)  # Перевіряємо кожну хвилину
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Помилка моніторингу системи: {e}")
                await asyncio.sleep(1) 