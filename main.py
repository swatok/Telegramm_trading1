"""
Головний файл для запуску торгового бота
"""

import os
import asyncio
from loguru import logger
from dotenv import load_dotenv

from api.jupiter import JupiterAPI
from api.quicknode import QuicknodeAPI
from database import (
    PositionRepository,
    TradeRepository,
    TransactionRepository
)
from trading.trade_orchestrator import TradeOrchestrator
from trading.wallet_account_manager import WalletAccountManager
from trading.wallet_balance_manager import WalletBalanceManager

# Завантажуємо змінні середовища
load_dotenv()

class TradingBot:
    """Головний клас торгового бота"""
    
    def __init__(self):
        """Ініціалізація бота"""
        # Ініціалізуємо API клієнти
        self.jupiter_api = JupiterAPI(os.getenv('JUPITER_API_KEY'))
        self.quicknode_api = QuicknodeAPI(os.getenv('QUICKNODE_API_KEY'))
        
        # Ініціалізуємо репозиторії
        self.position_repo = PositionRepository()
        self.trade_repo = TradeRepository()
        self.transaction_repo = TransactionRepository()
        
        # Отримуємо адресу гаманця
        self.wallet_address = os.getenv('WALLET_ADDRESS')
        
        # Ініціалізуємо менеджери гаманця
        self.wallet_balance_manager = WalletBalanceManager(
            self.quicknode_api,
            self.jupiter_api,
            self.wallet_address
        )
        self.wallet_account_manager = WalletAccountManager(
            self.quicknode_api,
            self.jupiter_api,
            self.wallet_address
        )
        
        # Ініціалізуємо координатор торгівлі
        self.trade_orchestrator = TradeOrchestrator(
            self.jupiter_api,
            self.quicknode_api,
            self.position_repo,
            self.trade_repo,
            self.transaction_repo,
            self.wallet_address,
            self._handle_log
        )
        
    async def start(self):
        """Запуск бота"""
        try:
            logger.info("Починаємо запуск торгового бота...")
            
            # Перевіряємо баланси
            await self.wallet_balance_manager.update_balances()
            total_balance = await self.wallet_balance_manager.get_total_balance()
            logger.info(f"Загальний баланс: {total_balance}")
            
            # Закриваємо порожні акаунти
            closed_accounts = await self.wallet_account_manager.close_empty_accounts()
            if closed_accounts:
                logger.info(f"Закрито порожніх акаунтів: {len(closed_accounts)}")
            
            # Запускаємо координатор торгівлі
            if await self.trade_orchestrator.start():
                logger.info("Торговий бот успішно запущено")
                
                # Очікуємо на сигнал завершення
                while True:
                    await asyncio.sleep(1)
            else:
                logger.error("Помилка запуску торгового бота")
                
        except KeyboardInterrupt:
            logger.info("Отримано сигнал завершення")
        except Exception as e:
            logger.error(f"Критична помилка: {e}")
        finally:
            await self.stop()
            
    async def stop(self):
        """Зупинка бота"""
        try:
            logger.info("Зупиняємо торгового бота...")
            await self.trade_orchestrator.stop()
            logger.info("Торговий бот успішно зупинено")
        except Exception as e:
            logger.error(f"Помилка при зупинці бота: {e}")
            
    def _handle_log(self, message: str):
        """Обробка логів від координатора"""
        logger.info(message)
            
async def main():
    """Головна функція"""
    bot = TradingBot()
    await bot.start()
    
if __name__ == "__main__":
    # Налаштовуємо логування
    logger.add(
        "logs/trading_bot.log",
        rotation="1 day",
        retention="7 days",
        level="INFO"
    )
    
    # Запускаємо бота
    asyncio.run(main())