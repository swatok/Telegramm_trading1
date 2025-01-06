"""
Модуль для обробки торгових сигналів.
Відповідає за обробку та виконання торгових сигналів.
"""

from decimal import Decimal
from typing import Dict, Optional
from datetime import datetime

from .constants import MIN_SOL_BALANCE, POSITION_SIZE_PERCENT
from .wallet_manager import WalletManager
from .price_monitor import PriceMonitor
from .token_validator import TokenValidator
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class TradeSignalHandler:
    """
    Клас для обробки торгових сигналів.
    Координує процес обробки та виконання торгових сигналів.
    """

    def __init__(
        self,
        wallet_manager: WalletManager,
        price_monitor: PriceMonitor,
        token_validator: TokenValidator,
        send_log_callback
    ):
        """
        Ініціалізація обробника сигналів.

        Args:
            wallet_manager: Менеджер гаманця
            price_monitor: Монітор цін
            token_validator: Валідатор токенів
            send_log_callback: Функція для відправки логів
        """
        self.wallet_manager = wallet_manager
        self.price_monitor = price_monitor
        self.token_validator = token_validator
        self.send_log = send_log_callback

    async def handle_signal(self, signal: Dict) -> bool:
        """
        Обробка торгового сигналу.

        Args:
            signal: Словник з даними сигналу

        Returns:
            True якщо сигнал успішно оброблено, False інакше
        """
        try:
            logger.info(f"Починаємо обробку сигналу: {signal}")
            await self.send_log("🔄 Обробка торгового сигналу...")

            # Перевіряємо баланс
            balance_data = await self.wallet_manager.get_total_balance()
            if not balance_data:
                await self.send_log("❌ Не вдалося отримати баланс")
                return False

            sol_balance = Decimal(str(balance_data['sol_balance']))
            logger.info(f"Поточний баланс: {balance_data}")
            await self.send_log(f"💰 Поточний баланс: {sol_balance:.4f} SOL (Всього: {balance_data['total_value_sol']:.4f} SOL)")

            if sol_balance < MIN_SOL_BALANCE:
                logger.error(f"Недостатньо SOL для торгівлі. Баланс: {sol_balance}")
                await self.send_log(f"❌ Недостатньо SOL для торгівлі: {sol_balance}")
                return False

            # Валідація токену
            token_address = signal.get('token_address')
            if not token_address:
                await self.send_log("❌ Не вказано адресу токену")
                return False

            validation_result = await self.token_validator.validate_token(token_address)
            if not validation_result['valid']:
                await self.send_log(f"❌ Токен не пройшов валідацію: {validation_result['reason']}")
                return False

            # Перевірка ціни та ліквідності
            price_data = await self.price_monitor.get_current_price(token_address)
            if not price_data:
                await self.send_log("❌ Не вдалося отримати ціну токену")
                return False

            if not self.price_monitor.has_sufficient_liquidity(token_address):
                await self.send_log("❌ Недостатня ліквідність")
                return False

            # Розрахунок розміру позиції
            position_size = sol_balance * POSITION_SIZE_PERCENT
            if position_size <= MIN_SOL_BALANCE:
                await self.send_log("❌ Розмір позиції занадто малий")
                return False

            # Виконання торгової операції
            success = await self._execute_trade(token_address, position_size, signal)
            if success:
                await self.send_log("✅ Торгова операція виконана успішно")
                return True
            else:
                await self.send_log("❌ Помилка виконання торгової операції")
                return False

        except Exception as e:
            logger.error(f"Помилка обробки сигналу: {e}")
            await self.send_log(f"❌ Помилка: {str(e)}")
            return False

    async def _execute_trade(self, token_address: str, amount: Decimal, signal: Dict) -> bool:
        """
        Виконання торгової операції.

        Args:
            token_address: Адреса токену
            amount: Розмір позиції
            signal: Дані сигналу

        Returns:
            True якщо операція успішна, False інакше
        """
        try:
            # Перевірка достатності балансу
            if not await self.wallet_manager.has_sufficient_balance(amount):
                logger.error("Недостатньо коштів для виконання операції")
                return False

            # Обгортання SOL в WSOL якщо потрібно
            tx_hash = await self.wallet_manager.wrap_sol(amount)
            if not tx_hash:
                logger.error("Помилка обгортання SOL")
                return False

            # Тут буде виклик методу для виконання свопу
            # Залежить від конкретної реалізації DEX API

            logger.info(f"Торгова операція виконана успішно: {tx_hash}")
            return True

        except Exception as e:
            logger.error(f"Помилка виконання торгової операції: {e}")
            return False

    async def validate_signal(self, signal: Dict) -> Dict[str, bool]:
        """
        Валідація торгового сигналу.

        Args:
            signal: Дані сигналу

        Returns:
            Словник з результатами валідації
        """
        results = {
            'valid': True,
            'checks': {
                'has_token_address': False,
                'has_valid_token': False,
                'has_sufficient_balance': False,
                'has_sufficient_liquidity': False
            }
        }

        try:
            # Перевірка наявності адреси токену
            token_address = signal.get('token_address')
            results['checks']['has_token_address'] = bool(token_address)
            if not token_address:
                results['valid'] = False
                return results

            # Валідація токену
            token_validation = await self.token_validator.validate_token(token_address)
            results['checks']['has_valid_token'] = token_validation['valid']
            if not token_validation['valid']:
                results['valid'] = False
                return results

            # Перевірка балансу
            balance = await self.wallet_manager.get_balance()
            results['checks']['has_sufficient_balance'] = balance >= MIN_SOL_BALANCE
            if not results['checks']['has_sufficient_balance']:
                results['valid'] = False
                return results

            # Перевірка ліквідності
            results['checks']['has_sufficient_liquidity'] = (
                self.price_monitor.has_sufficient_liquidity(token_address)
            )
            if not results['checks']['has_sufficient_liquidity']:
                results['valid'] = False
                return results

            return results

        except Exception as e:
            logger.error(f"Помилка валідації сигналу: {e}")
            results['valid'] = False
            return results 