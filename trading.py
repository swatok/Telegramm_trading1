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

from api.jupiter import JupiterAPI
from api.quicknode import QuicknodeAPI
from model.transaction import Transaction
from model.quote import Quote
from model.position import Position
from model.wallet_activity import WalletActivity
from model.bot_session import BotSession
from model.trade_stats import TradeStats

WSOL_ADDRESS = "So11111111111111111111111111111111111111112"
MIN_SOL_BALANCE = Decimal("0.02")  # Мінімальний баланс SOL для операцій

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
        
        # Історія активності
        self.activities = []
        
    async def start(self, telegram_client):
        """Ініціалізація клієнта"""
        self.client = telegram_client
        
        # Перевіряємо баланс при старті
        balance = await self.quicknode.get_sol_balance()
        logger.info(f"Початковий баланс: {balance:.4f} SOL")
        
        # Записуємо активність гаманця
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
        
        await self.send_log(
            f"🚀 Торговий виконавець запущено\n"
            f"💰 Баланс гаманця: {balance:.4f} SOL\n"
            f"🔑 Адреса: {self.keypair.pubkey()}\n"
            f"📊 Сесія: {self.session.id[:8]}"
        )
        
    async def send_log(self, message: str):
        """Відправка логу в Telegram канал"""
        try:
            monitor_channel = int(os.getenv('MONITOR_CHANNEL_ID'))
            await self.client.send_message(monitor_channel, message)
            logger.debug(f"Відправлено повідомлення в канал {monitor_channel}: {message}")
        except Exception as e:
            logger.error(f"Помилка відправки логу: {e}")
            self.session.add_error("Помилка відправки логу", {"error": str(e)})
            
    async def handle_trade_signal(self, signal):
        """Обробка торгового сигналу"""
        try:
            logger.info(f"Починаємо обробку сигналу для токена {signal.token_address}")
            self.session.processed_signals += 1
            signal.update_status('processing')
            
            # Перевіряємо баланс
            balance = await self.quicknode.get_sol_balance()
            if balance is None:
                signal.update_status('failed', "Помилка отримання балансу")
                self.session.add_error("Помилка отримання балансу")
                await self.send_log("❌ Помилка отримання балансу")
                return
                
            logger.info(f"Поточний баланс: {balance:.4f} SOL")
            
            if Decimal(str(balance)) < MIN_SOL_BALANCE:
                signal.update_status('failed', f"Недостатньо коштів: {balance} SOL")
                self.session.add_warning("Недостатньо коштів", {
                    "balance": str(balance),
                    "required": str(MIN_SOL_BALANCE)
                })
                await self.send_log(
                    f"⚠️ Недостатньо коштів для свопу\n"
                    f"Необхідно: {MIN_SOL_BALANCE} SOL\n"
                    f"Доступно: {balance:.4f} SOL"
                )
                return
                
            # Перевіряємо токен
            is_available = await self.quicknode.verify_token(signal.token_address)
            if not is_available:
                signal.update_status('failed', "Токен не знайдено в мережі")
                self.session.add_warning("Токен не знайдено", {
                    "token_address": signal.token_address
                })
                await self.send_log(f"❌ Токен не знайдено: {signal.token_address}")
                return
                
            # Отримуємо котирування
            logger.info("Запит котирування від Jupiter")
            quote_data = await self.jupiter.get_quote(
                input_mint=WSOL_ADDRESS,
                output_mint=signal.token_address,
                amount=float(signal.amount_sol),  # Використовуємо amount_sol з сигналу
                slippage_bps=int(signal.slippage * 100)  # Конвертуємо % в bps
            )
            
            if not quote_data:
                signal.update_status('failed', "Помилка отримання котирування")
                self.session.add_error("Помилка отримання котирування")
                await self.send_log(f"❌ Помилка отримання котирування для токена")
                return
                
            # Створюємо об'єкт Quote
            quote = Quote(
                input_mint=WSOL_ADDRESS,
                output_mint=signal.token_address,
                in_amount=signal.amount_sol,
                out_amount=Decimal(str(quote_data['outAmount'])),
                price_impact=Decimal(str(quote_data.get('priceImpact', 0))),
                slippage=signal.slippage,
                route_plan=quote_data['routePlan'],
                other_amount_threshold=Decimal(str(quote_data['otherAmountThreshold'])),
                swap_mode=quote_data.get('swapMode', 'ExactIn')
            )
            
            # Виконуємо своп
            signature = await self.jupiter.sign_and_send(quote_data, self.keypair)
            if signature:
                # Створюємо транзакцію
                tx = Transaction(
                    signature=signature,
                    status='pending',
                    timestamp=datetime.now(),
                    token_address=signal.token_address,
                    amount=quote.in_amount,
                    type='swap',
                    swap_info={
                        'input_mint': quote.input_mint,
                        'output_mint': quote.output_mint,
                        'price_impact': float(quote.price_impact)
                    },
                    input_amount=quote.in_amount,
                    output_amount=quote.out_amount,
                    price_impact=quote.price_impact
                )
                
                logger.info(f"Своп успішний: {signature}")
                
                # Перевіряє��о нові баланси
                new_balance = await self.quicknode.get_sol_balance()
                new_token_balance = await self.quicknode.get_token_balance(signal.token_address)
                
                # Записуємо активність гаманця
                activity = WalletActivity(
                    wallet_address=str(self.keypair.pubkey()),
                    activity_type='swap',
                    token_address=signal.token_address,
                    amount=quote.in_amount,
                    timestamp=datetime.now(),
                    transaction_signature=signature,
                    token_symbol=signal.token.symbol,
                    price_impact=quote.price_impact,
                    slippage=quote.slippage,
                    swap_info={
                        'input_mint': quote.input_mint,
                        'output_mint': quote.output_mint,
                        'route_plan': quote.route_plan
                    }
                )
                self.activities.append(activity)
                
                # Оновлюємо статус сигналу
                signal.update_status('executed')
                signal.transaction_signature = signature
                signal.execution_price = quote.price
                
                # Оновлюємо статистику
                self.session.successful_trades += 1
                self.session.total_volume += quote.in_amount
                
                # Додаємо в статистику
                self.stats.add_trade(
                    token=signal.token_address,
                    amount=quote.in_amount,
                    profit=Decimal("0"),  # Поки що не рахуємо
                    fees=quote.total_fee_amount,
                    timestamp=datetime.now(),
                    success=True
                )
                
                await self.send_log(
                    f"✅ Своп успішно виконано!\n"
                    f"- Новий баланс SOL: {new_balance:.4f}\n"
                    f"- Баланс токена: {new_token_balance:.9f}\n"
                    f"- Транзакція: https://solscan.io/tx/{signature}"
                )
            else:
                signal.update_status('failed', "Помилка виконання свопу")
                self.session.failed_trades += 1
                self.session.add_error("Помилка виконання свопу")
                await self.send_log("❌ Помилка виконання свопу")
                
        except Exception as e:
            logger.error(f"Помилка обробки сигналу: {e}", exc_info=True)
            signal.update_status('failed', str(e))
            self.session.add_error("Помилка обробки сигналу", {"error": str(e)})
            await self.send_log(f"❌ Помилка: {str(e)}")
            
    async def stop(self):
        """Зупинка торгового виконавця"""
        self.session.stop("Manual stop")
        await self.send_log(
            f"🛑 Торговий виконавець зупинено\n"
            f"📊 Статистика сесії:\n"
            f"- Оброблено сигналів: {self.session.processed_signals}\n"
            f"- Успішних угод: {self.session.successful_trades}\n"
            f"- Невдалих угод: {self.session.failed_trades}\n"
            f"- Загальний об'єм: {float(self.session.total_volume):.4f} SOL"
        )
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
        """Дест��уктор"""
        # Не використовуємо await тут, оскільки це синхронний метод
        pass