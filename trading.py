"""
Модуль для виконання торгових операцій
"""

import os
from datetime import datetime
import uuid
from dotenv import load_dotenv
from solders.keypair import Keypair
import base58
from loguru import logger
from decimal import Decimal
import asyncio
from typing import Optional

from api.jupiter import JupiterAPI
from api.quicknode import QuicknodeAPI
from model.transaction import Transaction
from model.quote import Quote
from model.position import Position
from model.wallet_activity import WalletActivity
from model.bot_session import BotSession
from model.trade_stats import TradeStats

# Константи
WSOL_ADDRESS = "So11111111111111111111111111111111111111112"
MIN_SOL_BALANCE = Decimal("0.02")  # Мінімальний баланс SOL для операцій
TRANSACTION_CONFIRMATION_TIMEOUT = 60  # Таймаут очікування підтвердження транзакції в секундах

# Take-profit рівні
TAKE_PROFIT_LEVELS = [
    {"level": Decimal("1"), "sell_percent": Decimal("20")},   # 100% - продаж 20%
    {"level": Decimal("2.5"), "sell_percent": Decimal("20")}, # 250% - продаж 20%
    {"level": Decimal("5"), "sell_percent": Decimal("20")},   # 500% - продаж 20%
    {"level": Decimal("10"), "sell_percent": Decimal("20")},  # 1000% - продаж 20%
    {"level": Decimal("30"), "sell_percent": Decimal("25")},  # 3000% - продаж 25%
    {"level": Decimal("90"), "sell_percent": Decimal("50")}   # 9000% - продаж 50%
]

# Stop-loss рівень
STOP_LOSS_LEVEL = Decimal("-0.75")  # -75%

class TradingExecutor:
    def __init__(self):
        load_dotenv()
        self.private_key = os.getenv('SOLANA_PRIVATE_KEY')
        if not self.private_key:
            raise ValueError("Відсутній SOLANA_PRIVATE_KEY")
        self.keypair = Keypair.from_bytes(base58.b58decode(self.private_key))
        
        # Ініціалізуємо API клієнти
        self.quicknode = QuicknodeAPI()
        self.jupiter = JupiterAPI()
        self.client = None
        
        # Створюємо сесію бота
        self.session = BotSession(
            id=str(uuid.uuid4()),
            start_time=datetime.now(),
            status='running'
        )
        
        # Створюємо статистику
        self.stats = TradeStats(
            period='day',
            start_time=datetime.now()
        )
        
        # Активні позиції та їх моніторинг
        self.active_positions = {}  # token_address -> Position
        
        # Історія активності
        self.activities = []
        
    async def wait_for_transaction_confirmation(self, signature: str, max_attempts: int = 30) -> bool:
        """Очікування підтвердження транзакції"""
        attempt = 1
        wait_time = 1  # початковий час очікування в секундах
        
        while attempt <= max_attempts:
            logger.info(f"Спроба {attempt}: Перевірка статусу транзакції {signature}")
            
            status = await self.quicknode.get_transaction_status(signature)
            logger.info(f"Отримано статус: {status}")
            
            if status == 'confirmed':
                # Отримуємо баланс після транзакції
                new_balance = await self.quicknode.get_sol_balance(str(self.keypair.pubkey()))
                logger.info(f"Новий баланс після транзакції: {new_balance:.9f} SOL")
                
                # Відправляємо повідомлення про успішне підтвердження
                await self.send_log(
                    f"✅ Транзакція підтверджена!\n"
                    f"• Підпис: {signature}\n"
                    f"• Посилання: https://solscan.io/tx/{signature}\n"
                    f"• Новий баланс: {new_balance:.9f} SOL"
                )
                return True
                
            elif status == 'failed':
                error_msg = f"❌ Транзакція не вдалася: {signature}"
                logger.error(error_msg)
                await self.send_log(
                    f"{error_msg}\n"
                    f"• Посилання: https://solscan.io/tx/{signature}"
                )
                return False
                
            elif status == 'pending':
                await self.send_log(
                    f"⏳ Очікування підтвердження транзакції...\n"
                    f"• Спроба: {attempt}/{max_attempts}\n"
                    f"• Підпис: {signature}\n"
                    f"• Посилання: https://solscan.io/tx/{signature}"
                )
                
                # Збільшуємо час очікування експоненційно
                logger.info(f"Чекаємо {wait_time} секунд перед наступною спробою...")
                await asyncio.sleep(wait_time)
                wait_time = min(wait_time * 2, 10)  # максимум 10 секунд
                attempt += 1
                continue
                
            else:
                error_msg = f"❌ Помилка перевірки статусу транзакції: {signature}"
                logger.error(error_msg)
                await self.send_log(
                    f"{error_msg}\n"
                    f"• Посилання: https://solscan.io/tx/{signature}"
                )
                return False
        
        error_msg = f"❌ Перевищено максимальну кількість спроб ({max_attempts}) для транзакції {signature}"
        logger.error(error_msg)
        await self.send_log(
            f"{error_msg}\n"
            f"• Посилання: https://solscan.io/tx/{signature}"
        )
        return False
        
    async def monitor_position(self, position: Position):
        """Моніторинг позиції для take-profit та stop-loss"""
        try:
            # Отримуємо поточну ціну в SOL
            quote_data = await self.jupiter.get_quote(
                input_mint=position.token_address,
                output_mint=WSOL_ADDRESS,
                amount=int(float(position.amount) * 1e9),  # Конвертуємо в лампорти
                slippage_bps=100
            )
            
            if not quote_data:
                return
                
            current_value = Decimal(str(quote_data['outAmount']))
            profit_percent = (current_value - position.initial_value) / position.initial_value
            
            # Перевіряємо stop-loss
            if profit_percent <= STOP_LOSS_LEVEL:
                await self.execute_exit(position, position.remaining_amount, "stop_loss")
                return
                
            # Перевіряємо take-profit рівні
            for tp_level in TAKE_PROFIT_LEVELS:
                if profit_percent >= tp_level["level"] and not position.is_level_triggered(tp_level["level"]):
                    sell_amount = position.remaining_amount * tp_level["sell_percent"] / Decimal("100")
                    await self.execute_exit(position, sell_amount, f"take_profit_{tp_level['level']}x")
                    position.mark_level_triggered(tp_level["level"])
                    
        except Exception as e:
            logger.error(f"Помилка моніторингу позиції: {e}")

    async def execute_exit(self, position: Position, amount: Decimal, reason: str):
        """Виконання виходу з позиції"""
        try:
            logger.info(f"Виконуємо вихід з позиції: {amount} токенів, причина: {reason}")
            
            quote_data = await self.jupiter.get_quote(
                input_mint=position.token_address,
                output_mint=WSOL_ADDRESS,
                amount=int(float(amount) * 1e9),  # Конвертуємо в лампорти
                slippage_bps=100
            )
            
            if not quote_data:
                logger.error("Не вдалося отримати котирування для виходу")
                return
                
            signature = await self.jupiter.sign_and_send(quote_data, self.keypair)
            if signature:
                # Чекаємо підтвердження транзакції
                status = await self.wait_for_transaction_confirmation(signature)
                if status == "confirmed":
                    position.remaining_amount -= amount
                    await self.send_log(
                        f"🔄 Частковий вихід з ��озиції:\n"
                        f"• Токен: {position.token_address}\n"
                        f"• Причина: {reason}\n"
                        f"• Продано: {amount}\n"
                        f"• Транзакція: https://solscan.io/tx/{signature}"
                    )
                else:
                    await self.send_log(
                        f"❌ Помилка виходу з позиції:\n"
                        f"• Токен: {position.token_address}\n"
                        f"• Статус: {status}\n"
                        f"• Транзакція: https://solscan.io/tx/{signature}"
                    )
                
        except Exception as e:
            logger.error(f"Помилка виходу з позиції: {e}")

    async def start(self, telegram_client):
        """Ініціалізація клієнта"""
        self.client = telegram_client
        
        try:
            # Перевіряємо баланс SOL
            balance = await self.quicknode.get_sol_balance()
            logger.info(f"Початковий баланс SOL: {balance:.4f}")
            
            # Отримуємо всі токени
            tokens = await self.quicknode.get_all_tokens()
            logger.info(f"Знайдено {len(tokens)} токенів на гаманці")
            
            # Формуємо повідомлення
            message = [
                "🚀 Торговий виконавець запущено",
                f"💰 Баланс SOL: {balance:.4f}",
                f"🔑 Адреса: {self.keypair.pubkey()}",
                f"📊 Сесія: {self.session.id[:8]}",
                "\n📝 Токени на гаманці:"
            ]
            
            for token in tokens:
                message.append(
                    f"• {token['symbol']}: {token['balance']:.{token['decimals']}f}"
                    f"\n  └ Адреса: {token['mint']}"
                )
                
            # Записуємо активість гаманця
            activity = WalletActivity(
                wallet_address=str(self.keypair.pubkey()),
                activity_type='check',
                token_address=WSOL_ADDRESS,
                amount=Decimal(str(balance)),
                timestamp=datetime.now(),
                transaction_signature='',
                token_symbol='SOL'
            )
            
            self.activities.append(activity)
            
            # Відправляємо повідомлен��я в лог
            await self.send_log("\n".join(message))
            
        except Exception as e:
            error_msg = f"❌ Помилка при запуску:\n{str(e)}"
            logger.error(error_msg)
            await self.send_log(error_msg)
            
    async def handle_trade_signal(self, signal):
        """Обробка торгового сигналу"""
        try:
            logger.info(f"1. Отримано сигнал для токена {signal.token_address}")
            self.session.processed_signals += 1
            signal.update_status('processing')
            
            # 2. Перевіряємо баланс
            balance = await self.quicknode.get_sol_balance()
            if balance is None or balance < MIN_SOL_BALANCE:
                error_msg = f"❌ Недостатньо коштів: {balance:.4f} SOL"
                signal.update_status('failed', error_msg)
                await self.send_log(error_msg)
                return
            logger.info(f"2. Перевірка балансу: {balance:.4f} SOL")
            
            # 3. Перевіряємо існування токена
            if not await self.quicknode.verify_token(signal.token_address):
                error_msg = "❌ Токен не існує або не є SPL токеном"
                signal.update_status('failed', error_msg)
                await self.send_log(error_msg)
                return
            logger.info("3. Токен успішно верифіковано")
            
            # 4. Отримуємо інформацію про токен
            token_info = await self.quicknode.get_token_info(signal.token_address)
            token_symbol = "Unknown"
            token_name = "Unknown Token"
            
            if token_info:
                token_symbol = token_info.get('symbol', 'Unknown')
                token_name = token_info.get('name', 'Unknown Token')
                logger.info(f"4. Інформація про токен: {token_symbol} ({token_name})")
            else:
                logger.warning("4. Не вдалося отримати інформацію про токен")
                
            # 5. Розраховуємо розмір позиції (5% від балансу)
            position_size = Decimal(str(balance)) * Decimal(str(os.getenv('INITIAL_POSITION_PERCENT', '5'))) / Decimal('100')
            signal.amount_sol = position_size
            logger.info(f"5. Розмір позиції: {position_size:.6f} SOL")
            
            # 6. Отримуємо котирування
            quote_data = await self.jupiter.get_quote(
                input_mint=WSOL_ADDRESS,
                output_mint=signal.token_address,
                amount=int(float(position_size) * 1e9),  # Конвертуємо в лампорти
                slippage_bps=100
            )
            
            if not quote_data:
                error_msg = "❌ Не вдалося отримати котирування"
                signal.update_status('failed', error_msg)
                await self.send_log(error_msg)
                return
            logger.info("6. Котирування успішно отримано")
            
            # 7. Виконуємо своп
            logger.info("7. Виконуємо своп...")
            signature = await self.jupiter.sign_and_send(quote_data, self.keypair)
            if not signature:
                error_msg = "❌ Помилка виконання транзакції"
                signal.update_status('failed', error_msg)
                await self.send_log(error_msg)
                return
                
            # 8. Чекаємо підтвердження транзакції
            status = await self.wait_for_transaction_confirmation(signature)
            if status == "confirmed":
                # Створюємо нову позицію
                position = Position(
                    token_address=signal.token_address,
                    initial_amount=Decimal(str(quote_data['outAmount'])),
                    initial_value=position_size,
                    entry_price=position_size / Decimal(str(quote_data['outAmount'])),
                    timestamp=datetime.now()
                )
                
                # Додаємо позицію до активних
                self.active_positions[signal.token_address] = position
                
                # Оновлюємо статус сигналу
                signal.update_status('executed')
                
                # Записуємо активність
                activity = WalletActivity(
                    wallet_address=str(self.keypair.pubkey()),
                    activity_type='buy',
                    token_address=signal.token_address,
                    amount=position.initial_amount,
                    timestamp=datetime.now(),
                    transaction_signature=signature,
                    token_symbol=token_symbol
                )
                self.activities.append(activity)
                
                # Відправляємо повідомлення про успішну покупку
                await self.send_log(
                    f"✅ Успішна покупка:\n"
                    f"• Токен: {token_symbol} ({signal.token_address})\n"
                    f"• Сума: {position_size:.6f} SOL\n"
                    f"• Отримано: {position.initial_amount:.6f} токенів\n"
                    f"• Ціна входу: {position.entry_price:.12f} SOL\n"
                    f"• Транзакція: https://solscan.io/tx/{signature}"
                )
                
                # Запускаємо моніторинг позиції
                asyncio.create_task(self.monitor_position(position))
                
            else:
                error_msg = f"❌ Помилка підтвердження транзакції (статус: {status})"
                signal.update_status('failed', error_msg)
                await self.send_log(error_msg)
                
        except Exception as e:
            error_msg = f"❌ Помилка обробки сигналу: {str(e)}"
            logger.error(error_msg)
            signal.update_status('failed', error_msg)
            await self.send_log(error_msg)
            
    async def send_log(self, message: str):
        """Відправка логу в Telegram канал"""
        try:
            monitor_channel = int(os.getenv('MONITOR_CHANNEL_ID'))
            await self.client.send_message(monitor_channel, message)
            logger.debug(f"Відправлено повідомлення в канал {monitor_channel}")
        except Exception as e:
            logger.error(f"Помилка відправки логу: {e}")
            self.session.add_error("Помилка відправки логу", {"error": str(e)})
            
    async def stop(self):
        """Зупинка торгового виконавця"""
        try:
            self.session.stop("Manual stop")
            
            # Отримуємо фінальні баланси
            final_balance = await self.quicknode.get_sol_balance()
            tokens = await self.quicknode.get_all_tokens()
            
            message = [
                "🛑 Торговий виконавець зупинено",
                "\n📊 Статистика сесії:",
                f"• Оброблено сигналів: {self.session.processed_signals}",
                f"• Успішних угод: {self.session.successful_trades}",
                f"• Невдалих угод: {self.session.failed_trades}",
                f"• Загальний об'єм: {float(self.session.total_volume):.4f} SOL",
                "\n💰 Фінальні баланси:"
            ]
            
            message.append(f"• SOL: {final_balance:.4f}")
            for token in tokens:
                if token['mint'] != WSOL_ADDRESS:
                    message.append(
                        f"• {token['symbol']}: {token['balance']:.{token['decimals']}f}"
                    )
                    
            await self.send_log("\n".join(message))
            
        except Exception as e:
            error_msg = f"❌ Помилка при зупинці бота: {str(e)}"
            logger.error(error_msg)
            await self.send_log(error_msg)
            
        finally:
            # Закриваємо API клієнти
            await self.quicknode.close()
            await self.jupiter.close()
            
    async def cleanup(self):
        """Очищення ресурсів"""
        try:
            await self.quicknode.close()
            await self.jupiter.close()
        except Exception as e:
            logger.error(f"Помилка при очищенні ресурсів: {e}")
            
    def __del__(self):
        """Деструктор"""
        # Не використовуємо await тут, оскільки це синхронний метод
        pass