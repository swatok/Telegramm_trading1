"""
Модуль для виконання торгових операцій
"""

import os
import json
import asyncio
import aiohttp
import logging
from decimal import Decimal
from loguru import logger
from datetime import datetime
from typing import Dict, List, Optional
from contextlib import contextmanager
from solders.keypair import Keypair
import base58
import ssl
import time
import uuid

from api.jupiter import JupiterAPI
from api.quicknode import QuicknodeAPI
from model.transaction import Transaction
from model.quote import Quote
from model.position import Position
from model.wallet_activity import WalletActivity
from model.bot_session import BotSession
from model.trade_stats import TradeStats
from database import Database
from wallet import Wallet

logger = logging.getLogger(__name__)

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
    def __init__(self, db: Database, send_log_callback, ssl_context=None):
        """Ініціалізація торгового виконавця"""
        self.db = db
        self.send_log = send_log_callback
        self.ssl_context = ssl_context
        
        # Ініціалізуємо API клієнти
        self.quicknode = QuicknodeAPI(ssl_context=ssl_context)
        self.jupiter = JupiterAPI(ssl_context=ssl_context)
        
        # Ініціалізуємо гаманець
        if not os.getenv('SOLANA_PRIVATE_KEY'):
            raise ValueError("Не вказано SOLANA_PRIVATE_KEY")
            
        self.wallet = Wallet()
        
        # Створюємо ID сесії
        self.current_session_id = str(uuid.uuid4())
        
        # Ініціалізуємо сесію aiohttp
        self.session = None
        
        # Ініціалізуємо метрики продуктивності
        self.performance_metrics = {
            'api_calls': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'average_response_time': 0.0
        }
        
    async def __aenter__(self):
        """Створення сесії при вході в контекст"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закриття сесії при виході з контексту"""
        if self.session:
            await self.session.close()
            
    async def start(self):
        """Запуск торгового виконавця"""
        try:
            # Отримуємо початковий баланс
            balance = await self.get_balance()
            logger.info(f"Початковий баланс SOL: {balance}")
            await self.send_log(f"🔄 Початковий баланс: {balance:.4f} SOL")
            
            # Зберігаємо початковий баланс
            self.initial_balance = balance
            self.current_balance = balance
            
            # Позначаємо що виконавець запущений
            self.is_running = True
            
            logger.info("Торговий виконавець запущено")
            return True
            
        except Exception as e:
            logger.error(f"Помилка запуску торгового виконавця: {e}")
            raise
            
    async def stop(self):
        """Зупинка торгового виконавця"""
        try:
            self.is_running = False
            if self.session:
                await self.session.close()
            logger.info("Торговий виконавець зупинено")
        except Exception as e:
            logger.error(f"Помилка зупинки торгового виконавця: {e}")
            
    async def verify_token(self, token_address: str) -> bool:
        """Перевірка існування токена"""
        try:
            # Перевіряємо через QuickNode
            token_info = await self.quicknode.get_token_info(token_address)
            if not token_info:
                logger.error(f"Токен {token_address} не знайдено в QuickNode")
                return False
                
            # Перевіряємо можливість торгівлі через Jupiter
            try:
                price = await self.jupiter.get_price(token_address)
                if not price:
                    logger.error(f"Токен {token_address} недоступний для торгівлі в Jupiter")
                    return False
            except Exception as e:
                logger.error(f"Помилка отримання ціни з Jupiter: {e}")
                return False
                
            logger.info(f"Токен {token_address} успішно перевірено")
            return True
            
        except Exception as e:
            logger.error(f"Помилка перевірки токена: {e}")
            return False
            
    async def get_balance(self) -> Optional[Dict]:
        """Отримання балансу гаманця"""
        try:
            # Отримуємо баланс SOL
            sol_balance = await self.quicknode.get_sol_balance()
            if sol_balance is None:
                logger.error("Не вдалося отримати бала��с SOL")
                return None
                
            # Отримуємо всі токен-акаунти
            token_accounts = await self.quicknode.get_token_accounts()
            tokens = []
            total_value_sol = Decimal(str(sol_balance))  # Конвертуємо в Decimal для точних розрахунків
            
            if token_accounts:
                for account in token_accounts:
                    try:
                        token_address = account.get('mint')
                        if not token_address or token_address == WSOL_ADDRESS:
                            continue
                            
                        # Отримуємо баланс і decimals
                        raw_amount = Decimal(str(account.get('amount', '0')))
                        decimals = int(account.get('decimals', 9))
                        
                        # Конвертуємо баланс з урахуванням decimals
                        token_balance = raw_amount / Decimal(str(10 ** decimals))
                        
                        if token_balance <= 0:
                            continue
                            
                        # Отримуємо інформацію про токен
                        token_info = await self.jupiter.get_token_info(token_address)
                        if not token_info:
                            continue
                            
                        # Отримуємо ціну в SOL
                        price_in_sol = await self.jupiter.get_price(token_address, WSOL_ADDRESS)
                        if not price_in_sol:
                            continue
                            
                        # Розраховуємо вартість в SOL
                        price_decimal = Decimal(str(price_in_sol))
                        value_in_sol = token_balance * price_decimal
                        total_value_sol += value_in_sol
                        
                        tokens.append({
                            "address": token_address,
                            "symbol": token_info.get("symbol", "Unknown"),
                            "name": token_info.get("name", "Unknown Token"),
                            "balance": float(token_balance),
                            "price_sol": float(price_decimal),
                            "value_sol": float(value_in_sol)
                        })
                            
                    except Exception as e:
                        logger.error(f"Помилка обробки токену {token_address}: {str(e)}")
                        continue
                        
            return {
                "sol_balance": float(sol_balance),
                "total_value_sol": float(total_value_sol),
                "tokens": tokens
            }
            
        except Exception as e:
            logger.error(f"Помилка отримання балансу: {str(e)}")
            return None
            
    async def handle_trade_signal(self, signal: Dict) -> bool:
        """Обробка торгового сигналу"""
        try:
            logger.info(f"Починаємо обробку сигналу: {signal}")
            await self.send_log("🔄 Обробка торгового сигналу...")
            
            # Перевіряємо баланс
            balance = await self.get_balance()
            logger.info(f"Поточний баланс: {balance}")
            
            if not balance:
                await self.send_log("❌ Не вдалося отримати баланс")
                return False
                
            if balance.get('sol_balance', 0) < MIN_SOL_BALANCE:
                logger.error(f"Недостатньо SOL для торгівлі. Баланс: {balance.get('sol_balance', 0)}")
                await self.send_log(f"❌ Недостатньо SOL для торгівлі: {balance.get('sol_balance', 0)}")
                return False
                
            # Перевіряємо токен
            token_address = signal.get('token_address')
            if not token_address:
                logger.error("Відсутня адреса токена в сигналі")
                await self.send_log("❌ Відсутня адреса токена в сигналі")
                return False
                
            logger.info(f"Перевіряємо токен {token_address}")
            
            try:
                # Спочатку перевіряємо токен через QuickNode
                token_info = await self.quicknode.get_token_info(token_address)
                if not token_info:
                    logger.error(f"Не вдалося отримати інформацію про токен {token_address} через QuickNode")
                    await self.send_log("❌ Не вдалося отримати інформацію про токен")
                    return False
                    
                logger.info(f"Отримано інформацію про токен: {token_info}")
                
                # Спочатку робимо тестове котирування з малою сумою
                logger.info("Спроба отримати тестове котирування...")
                
                # Список параметрів для спроб
                test_params = [
                    {"amount": 100000, "slippage": 10.0},  # 0.0001 SOL, 10% slippage
                    {"amount": 500000, "slippage": 15.0},  # 0.0005 SOL, 15% slippage
                    {"amount": 1000000, "slippage": 20.0}, # 0.001 SOL, 20% slippage
                ]
                
                test_quote = None
                for params in test_params:
                    try:
                        logger.info(f"Спроба отримати тестове котирування з параметрами: {params}")
                        test_quote = await self.jupiter.get_quote(
                            input_mint=WSOL_ADDRESS,
                            amount=params["amount"],
                            output_mint=token_address,
                            slippage=params["slippage"]
                        )
                        
                        if test_quote:
                            logger.info(f"Тестове котирування отримано успішно з параметрами {params}")
                            await self.send_log(f"✅ Тестове котирування отримано успішно (amount={params['amount']/1e9} SOL, slippage={params['slippage']}%)")
                            break
                        else:
                            logger.warning(f"Не вдалося отримати тестове котирування з параметрами {params}")
                            
                    except Exception as e:
                        logger.error(f"Помилка при отриманні тестового котирування з параметрами {params}: {str(e)}")
                        continue
                
                if test_quote:
                    logger.info(f"Тестове котирування отримано успішно: {test_quote}")
                    
                    # Тепер пробуємо отримати реальне котирування
                    logger.info("Спроба отримати реальне котирування...")
                    
                    # Список параметрів для реального котирування
                    real_params = [
                        {"amount": 1000000, "slippage": 5.0},   # 0.001 SOL, 5% slippage
                        {"amount": 2000000, "slippage": 7.5},   # 0.002 SOL, 7.5% slippage
                        {"amount": 3000000, "slippage": 10.0},  # 0.003 SOL, 10% slippage
                    ]
                    
                    quote = None
                    for params in real_params:
                        try:
                            logger.info(f"Спроба отримати реальне котирування з параметрами: {params}")
                            quote = await self.jupiter.get_quote(
                                input_mint=WSOL_ADDRESS,
                                amount=params["amount"],
                                output_mint=token_address,
                                slippage=params["slippage"]
                            )
                            
                            if quote:
                                logger.info(f"Реальне котирування отримано успішно з параметрами {params}")
                                await self.send_log(f"✅ Реальне котирування отримано успішно (amount={params['amount']/1e9} SOL, slippage={params['slippage']}%)")
                                break
                            else:
                                logger.warning(f"Не вдалося отримати реальне котирування з параметрами {params}")
                                
                        except Exception as e:
                            logger.error(f"Помилка при отриманні реального котирування з параметрами {params}: {str(e)}")
                            continue
                    
                    if quote:
                        logger.info(f"Реальне котирування отримано: {quote}")
                        # Виводимо деталі роутингу
                        if quote.get("routePlan"):
                            routes = quote.get("routePlan", [])
                            route_info = "\n".join([f"• {route.get('swapInfo', {}).get('label', 'Unknown')}" for route in routes])
                            logger.info(f"Знайдено роути для торгівлі:\n{route_info}")
                            await self.send_log(f"📍 Знайдено роути для торгівлі:\n{route_info}")
                    else:
                        logger.error("Не вдалося отримати реальне котирування з жодними параметрами")
                        await self.send_log("❌ Не вдалося отримати реальне котирування")
                        return False
                else:
                    logger.error("Не вдалося отримати жодне тестове котирування")
                    await self.send_log("❌ Токен недоступний для торгівлі через Jupiter")
                    return False
                    
            except Exception as e:
                logger.error(f"Помилка при отриманні котирування: {str(e)}")
                await self.send_log(f"❌ Помилка при отриманні котирування: {str(e)}")
                return False
                
            # Перевіряємо ціну токена
            token_price = await self.jupiter.get_price(token_address)
            if not token_price:
                logger.error(f"Не вдалося отримати ціну токена {token_address}")
                await self.send_log("❌ Не вдалося отримати ціну токена")
                return False
                
            logger.info(f"Отримано ціну токена: {token_price}")
            
            # Перевіряємо чи ціна відповідає умовам
            expected_price = signal.get('price', 2)  # За замовчуванням очікуємо ціну 2
            price_diff = abs(token_price - expected_price) / expected_price
            logger.info(f"Поточна ціна: {token_price}, Очікувана ціна: {expected_price}, Різниця: {price_diff*100}%")
            if price_diff > 0.1:  # Допускаємо відхилення 10%
                logger.error(f"Ціна токена {token_price} значно відрізняється від очікуваної {expected_price}")
                await self.send_log(f"❌ Ціна токена {token_price} значно відрізняється від очікуваної {expected_price}")
                return False
                
            logger.info(f"Інформація про токен: {token_info}")
            await self.send_log(f"ℹ️ Токен: {token_info.get('name', 'Unknown')} ({token_info.get('symbol', 'Unknown')})")
            
            # Розраховуємо суму для покупки
            settings = self.db.get_settings()
            position_size = float(settings.get('position_size', 5)) / 100  # За замовчуванням 5%
            amount = int(float(balance['sol_balance']) * 1e9 * position_size)
            
            logger.info(f"Розрахована сума для покупки: {amount/1e9} SOL ({position_size*100}% від балансу)")
            await self.send_log(f"💱 Сума для покупки: {amount/1e9:.4f} SOL")
            
            # Отримуємо котирування
            try:
                logger.info("Отримуємо ф��нальне котирування для покупки...")
                quote = await self.jupiter.get_quote(
                    input_mint=WSOL_ADDRESS,
                    amount=amount,
                    slippage=float(settings.get('max_slippage', 1)),  # Slippage з налаштувань
                    output_mint=token_address
                )
                
                if quote:
                    logger.info(f"Отримано котирування: {quote}")
                else:
                    logger.error("Не вдалося отримати котирування для покупки")
                    await self.send_log("❌ Не вдалося отримати котирування для покупки")
                    return False
                    
            except Exception as e:
                logger.error(f"Помилка отримання котирування для покупки: {e}")
                await self.send_log("❌ Помилка отримання котирування для покупки")
                return False
                
            # Отримуємо транзакцію
            try:
                transaction = await self.jupiter.get_swap_transaction(quote)
            except Exception as e:
                logger.error(f"Помилка отримання транзакції: {e}")
                await self.send_log("❌ Помилка отримання транзакції")
                return False
                
            if not transaction:
                logger.error("Не вдалося отримати транзакцію")
                await self.send_log("❌ Не вдалося отримати транзакцію")
                return False
                
            logger.info("Транзакція отримана, виконуємо підпис та відправку")
            await self.send_log("📝 Підписуємо та відправляємо транзакцію...")
            
            # Виконуємо транзакцію
            signature = await self.execute_transaction_with_retry(
                transaction=transaction,
                required_sol=Decimal(str(amount / 1e9))
            )
            
            if not signature:
                logger.error("Не вдалося виконати транзакцію")
                await self.send_log("❌ Не вдалося виконати транзакцію")
                return False
                
            logger.info(f"Транзакція виконана успішно: {signature}")
            await self.send_log(f"✅ Транзакція виконана успішно: {signature}")
            
            # Зберігаємо позицію
            position_data = {
                'token_address': token_address,
                'token_symbol': token_info.get('symbol', 'Unknown'),
                'token_name': token_info.get('name', 'Unknown'),
                'entry_price': float(quote['price']),
                'amount': float(quote['outAmount']) / 1e9,
                'remaining_amount': float(quote['outAmount']) / 1e9,
                'transaction_signature': signature,
                'status': 'active',
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'tp_1_hit': False,
                'tp_2_hit': False,
                'tp_3_hit': False,
                'initial_value_sol': float(amount) / 1e9
            }
            
            try:
                position_id = self.db.add_position(position_data)
                logger.info(f"Створено нову позицію: {position_id}")
                await self.send_log(
                    f"📈 Створено нову позицію #{position_id}:\n"
                    f"• Токен: {token_info.get('name')} ({token_info.get('symbol')})\n"
                    f"• Ціна входу: {quote['price']:.6f} SOL\n"
                    f"• Кількість: {quote['outAmount']/1e9:.6f}\n"
                    f"• Вартість: {amount/1e9:.4f} SOL"
                )
            except Exception as e:
                logger.error(f"Помилка збереження позиції: {e}")
                await self.send_log("⚠️ Транзакція виконана, але не вдалося зберегти позицію")
            
            return True
            
        except Exception as e:
            logger.error(f"Помилка обробки сигналу: {str(e)}")
            await self.send_log(f"❌ Помилка: {str(e)}")
            return False
            
    async def execute_transaction_with_retry(self, transaction: Dict, required_sol: Decimal, max_retries: int = 3) -> Optional[str]:
        """Виконує транзакцію з повторними спробами"""
        try:
            for attempt in range(max_retries):
                try:
                    # Перевіряємо баланс перед виконанням
                    balance = await self.get_balance()
                    if not balance or Decimal(str(balance.get('sol_balance', 0))) < required_sol:
                        logger.error(f"Недостатньо SOL для транзакції. Потрібно: {required_sol}, Наявно: {balance.get('sol_balance', 0) if balance else 0}")
                        return None
                        
                    # Підписуємо та відправляємо транзакцію
                    signature = await self.quicknode.sign_and_send_transaction(transaction)
                    if not signature:
                        logger.error("Не вдалося підписати та відправити транзакцію")
                        continue
                        
                    logger.info(f"Транзакція відправлена: {signature}")
                    
                    # Чекаємо підтвердження
                    status = await self.quicknode.wait_for_confirmation(signature)
                    if status == 'confirmed':
                        logger.info(f"Транзакція {signature} підтверджена")
                        await self.send_log(f"✅ Транзакція підтверджена: {signature}")
                        return signature
                    elif status == 'failed':
                        logger.error(f"Транзакція {signature} не вдалася")
                        continue
                        
                except Exception as e:
                    logger.error(f"Помилка виконання транзакції (спроба {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1)  # Чекаємо перед повторною спробою
                    continue
                    
            logger.error("Вичерпано всі спроби виконання транзакції")
            return None
            
        except Exception as e:
            logger.error(f"Критична помилка виконання транзакції: {e}")
            return None
            
    async def monitor_positions(self):
        """Моніторинг відкритих позицій"""
        while True:
            try:
                # Отримуємо відкриті позиції
                positions = self.db.get_open_positions()
                if not positions:
                    await asyncio.sleep(30)
                    continue
                    
                logger.info(f"Моніторинг {len(positions)} відкритих позицій")
                
                for position in positions:
                    try:
                        # Отримуємо поточну ціну
                        price = await self.jupiter.get_price(position['token_address'])
                        if not price:
                            logger.error(f"Не вдалося отримати ціну для позиції {position['id']}")
                            continue
                            
                        # Розраховуємо PnL
                        entry_price = position['entry_price']
                        current_price = float(price)
                        pnl_percent = ((current_price - entry_price) / entry_price) * 100
                        
                        # Оновлюємо ціну в БД
                        self.db.update_position(position['id'], {
                            'current_price': current_price,
                            'pnl_percent': pnl_percent,
                            'updated_at': datetime.now()
                        })
                        
                        # Отримуємо налаштування
                        settings = self.db.get_settings()
                        tp_levels = [
                            float(settings.get('tp_1_percent', 20)),
                            float(settings.get('tp_2_percent', 20)),
                            float(settings.get('tp_3_percent', 20))
                        ]
                        sl_level = float(settings.get('stop_loss_level', -75))
                        
                        # Перевіряємо take-profit рівні
                        if not position['tp_1_hit'] and pnl_percent >= tp_levels[0]:
                            await self.execute_take_profit(position, 1, tp_levels[0])
                        elif not position['tp_2_hit'] and pnl_percent >= tp_levels[1]:
                            await self.execute_take_profit(position, 2, tp_levels[1])
                        elif not position['tp_3_hit'] and pnl_percent >= tp_levels[2]:
                            await self.execute_take_profit(position, 3, tp_levels[2])
                            
                        # Перевіряємо stop-loss
                        if pnl_percent <= sl_level:
                            await self.execute_stop_loss(position)
                            
                    except Exception as e:
                        logger.error(f"Помилка моніторингу позиції {position['id']}: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"Помилка моніторингу позицій: {e}")
                
            await asyncio.sleep(30)  # Перевіряємо кожні 30 секунд
            
    async def execute_take_profit(self, position: Dict, tp_level: int, tp_percent: float) -> bool:
        """Виконання take-profit"""
        try:
            # Розраховуємо суму для продажу
            remaining_amount = position['remaining_amount']
            sell_percent = 33.33  # Продаємо третину залишку на кожному TP
            amount_to_sell = remaining_amount * (sell_percent / 100)
            
            logger.info(f"Виконання TP{tp_level} для позиції {position['id']}")
            await self.send_log(
                f"🎯 Take-profit {tp_level} для {position['token_symbol']}:\n"
                f"• Прибуток: {tp_percent:.1f}%\n"
                f"• Продаж: {sell_percent:.1f}% позиції"
            )
            
            # Отримуємо квоту для ��родажу
            quote = await self.jupiter.get_quote(
                input_mint=position['token_address'],
                output_mint=WSOL_ADDRESS,
                amount=int(amount_to_sell * 1e9)
            )
            
            if not quote:
                logger.error(f"Не вдалося отримати квоту для TP{tp_level}")
                await self.send_log(f"❌ Не вдалося отримати квоту для TP{tp_level}")
                return False
                
            # Отримуємо транзакцію
            transaction = await self.jupiter.get_swap_transaction(quote)
            if not transaction:
                logger.error(f"Не вдалося отримати транзакцію для TP{tp_level}")
                await self.send_log(f"❌ Не вдалося отримати транзакцію для TP{tp_level}")
                return False
                
            # Виконуємо транзакцію
            signature = await self.execute_transaction_with_retry(
                transaction=transaction,
                required_sol=Decimal(str(quote['inAmount'] / 1e9))
            )
            
            if not signature:
                logger.error(f"Не вдалося виконати транзакцію TP{tp_level}")
                await self.send_log(f"❌ Не вдалося виконати транзакцію TP{tp_level}")
                return False
                
            # Оновлюємо позицію
            new_remaining = remaining_amount * (1 - sell_percent / 100)
            updates = {
                f'tp_{tp_level}_hit': True,
                f'tp_{tp_level}_price': float(quote['price']),
                f'tp_{tp_level}_transaction': signature,
                'remaining_amount': new_remaining,
                'updated_at': datetime.now()
            }
            
            self.db.update_position(position['id'], updates)
            
            logger.info(f"TP{tp_level} виконано успішно: {signature}")
            await self.send_log(
                f"✅ TP{tp_level} виконано успішно:\n"
                f"• Ціна продажу: {quote['price']:.6f} SOL\n"
                f"• Отримано: {quote['outAmount']/1e9:.4f} SOL\n"
                f"• Залишок позиції: {new_remaining:.6f}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Помилка виконання TP{tp_level}: {e}")
            await self.send_log(f"❌ Помилка виконан��я TP{tp_level}: {str(e)}")
            return False
            
    async def execute_stop_loss(self, position: Dict) -> bool:
        """Виконання stop-loss"""
        try:
            # Отримуємо квоту для продажу всієї позиції
            quote = await self.jupiter.get_quote(
                input_mint=position['token_address'],
                output_mint=WSOL_ADDRESS,
                amount=int(position['amount'] * 1e9)
            )
            
            if not quote:
                logger.error("Не вдалося отримати квоту для stop-loss")
                return False
                
            # Отримуємо транзакцію
            transaction = await self.jupiter.get_swap_transaction(quote)
            if not transaction:
                logger.error("Не вдалося отримати транзакцію для stop-loss")
                return False
                
            # Виконуємо транзакцію
            signature = await self.execute_transaction_with_retry(
                transaction=transaction,
                required_sol=Decimal(str(quote['inAmount'] / 1e9))
            )
            
            if not signature:
                logger.error("Не вдалося виконат�� транзакцію stop-loss")
                return False
                
            # Закриваємо позицію
            self.db.update_position(
                position['id'],
                {
                    'status': 'closed',
                    'exit_price': quote['outAmount'] / 1e9,
                    'exit_transaction': signature
                }
            )
            
            logger.info(f"Stop-loss виконано успішно: {signature}")
            return True
            
        except Exception as e:
            logger.error(f"Помилка виконання stop-loss: {e}")
            return False
