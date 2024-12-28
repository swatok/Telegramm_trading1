"""
Головний модуль бота для торгівлі на основі сигналів з Telegram
"""

import os
import json
import asyncio
from datetime import datetime
from telethon import TelegramClient, events
from dotenv import load_dotenv
from loguru import logger
from telethon.tl.custom import Button
import logging
import sys
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
import ssl

from message_parser import MessageParser
from trading import TradingExecutor
from config import setup_logging
from model.channel import Channel
from database import Database

# Налаштовуємо логування
setup_logging()

class TradingBot:
    def __init__(self, api_id, api_hash, bot_token):
        self.api_id = api_id
        self.api_hash = api_hash
        self.bot_token = bot_token
        self.db = Database()
        self.monitor_channel = None  # Буде встановлено пізніше
        
        # Створюємо SSL контекст
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Ініціалізуємо торговий виконавець
        self.trading_executor = TradingExecutor(
            db=self.db,
            send_log_callback=self.send_log,
            ssl_context=ssl_context
        )
        
        # Ініціалізуємо клієнти Telegram
        self.monitor_client = TelegramClient(
            session='monitor_session',
            api_id=self.api_id,
            api_hash=self.api_hash
        )
        
        self.bot_client = TelegramClient(
            session='bot_session',
            api_id=self.api_id,
            api_hash=self.api_hash
        )
        
        self.waiting_for = {}
        
    async def start(self):
        """Запуск бота"""
        try:
            # Налаштовуємо логування
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s | %(levelname)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            logging.getLogger('asyncio').setLevel(logging.WARNING)
            
            logger.info("Логування налаштовано")
            
            # Ініціалізуємо базу даних
            self.db = Database()
            logger.info("База даних ініціалізована")
            
            # Додаємо канали за замовчуванням
            await self.setup_default_channels()
            
            # Запускаємо клієнт моніторингу
            await self.monitor_client.start()
            logger.info("Клієнт моніторингу запущено")
            
            # Запускаємо клієнт бота
            await self.bot_client.start()
            logger.info("Клієнт бота запущено")
            
            # Реєструємо обробники подій
            self.register_handlers()
            logger.info("Обробники подій зареєстровано")
            
            # Ініціалізуємо торговий виконавець
            self.trading_executor = TradingExecutor(
                db=self.db,
                send_log_callback=self.send_log,
                ssl_context=None
            )
            
            # Запускаємо торговий виконавець
            await self.trading_executor.__aenter__()
            
            try:
                # Отримуємо початковий баланс
                balance = await self.trading_executor.get_balance()
                if balance:
                    logger.info(f"Початковий баланс SOL: {balance['sol_balance']}")
                
                logger.info("Торговий виконавець запущено")
                
                # Запускаємо основний цикл
                await asyncio.gather(
                    self.monitor_client.run_until_disconnected(),
                    self.bot_client.run_until_disconnected()
                )
                
            finally:
                # Закриваємо сесію при завершенні
                await self.trading_executor.__aexit__(None, None, None)
            
        except Exception as e:
            logger.error(f"Помилка запуску бота: {e}")
            raise
            
    async def stop(self):
        """Зпинка бота"""
        try:
            if self.monitor_client:
                await self.monitor_client.disconnect()
            if self.bot_client:
                await self.bot_client.disconnect()
            await self.trading_executor.stop()
            logger.info("Бот успішно зупинено")
        except Exception as e:
            logger.error(f"Помилка зупинки бота: {e}", exc_info=True)

    async def manage_channels(self, event):
        """Відображення меню керування каналами"""
        try:
            # Отримуємо список каналів
            channels = self.db.get_channels()
            
            # Формуємо повідомлення зі списком каналів
            message = "🔧 Керування каналами:\n\n"
            
            if not channels:
                message += "Немає доданих каналів"
            else:
                for channel in channels:
                    status_emoji = "✅" if channel["status"] == "active" else "❌"
                    message += f"{status_emoji} {channel['name']}\n"
                    
            # Формуємо кнопки для керування
            buttons = []
            buttons.append([Button.inline("➕ Додати канал", b"add_channel")])
            
            # Додаємо кнопки для кожного каналу
            for channel in channels:
                channel_name = channel["name"]
                buttons.append([
                    Button.inline(f"{'🔴 Деактивувати' if channel['status'] == 'active' else '🟢 Активувати'} {channel_name}", 
                                f"toggle_channel:{channel_name}".encode()),
                    Button.inline("❌", f"remove_channel:{channel_name}".encode())
                ])
                
            buttons.append([Button.inline("⬅️ Назад", b"main_menu")])
            
            # Відправляємо повідомлення
            await event.respond(message, buttons=buttons)
            
        except Exception as e:
            logger.error(f"Помилка відображення меню каналів: {e}")
            await event.respond("❌ Помилка відображення меню каналів")

    async def add_channel(self, channel_name: str) -> str:
        """Додавання нового каналу для моніторингу"""
        try:
            # Перевіряємо чи канал існує
            channel = await self.monitor_client.get_entity(channel_name)
            if not channel:
                return f"❌ Канал {channel_name} не знайдено"
                
            # Додаємо канал до бази даних
            channel_data = {
                "name": channel_name,
                "type": "trading",
                "status": "active",
                "settings": {}
            }
            if self.db.add_channel(channel_data):
                # Підключаємось до каналу
                await self.monitor_client(JoinChannelRequest(channel))
                return f"✅ Канал {channel_name} успішно додано"
            else:
                return f"❌ Канал {channel_name} вже існує"
                
        except Exception as e:
            logger.error(f"Помилка додавання каналу {channel_name}: {e}")
            return f"❌ Помилка додавання каналу: {str(e)}"
            
    async def remove_channel(self, channel_name: str) -> str:
        """Видалення каналу з моніторингу"""
        try:
            # Отримуємо канал з бази даних
            channel = self.db.get_channel_by_name(channel_name)
            if not channel:
                return f"❌ Канал {channel_name} не знайдено"
                
            # Видаляємо канал з бази даних
            if self.db.delete_channel(channel_name):
                # Відключаємось від каналу
                channel_entity = await self.monitor_client.get_entity(channel_name)
                await self.monitor_client(LeaveChannelRequest(channel_entity))
                return f"✅ Канал {channel_name} видалено"
            else:
                return f"❌ Помилка видалення каналу {channel_name}"
                
        except Exception as e:
            logger.error(f"Помилка видалення каналу {channel_name}: {e}")
            return f"❌ Помилка видалення каналу: {str(e)}"
            
    async def toggle_channel(self, channel_name: str) -> str:
        """Зміна статусу каналу (активний/неактивний)"""
        try:
            # Отримуємо канал з бази даних
            channel = self.db.get_channel_by_name(channel_name)
            if not channel:
                return f"❌ Канал {channel_name} не знайдено"
                
            # Змінюємо статус на протилежний
            new_status = "inactive" if channel["status"] == "active" else "active"
            
            # Оновлюємо статус в базі даних
            updates = {"status": new_status}
            if self.db.update_channel(channel_name, updates):
                status_emoji = "✅" if new_status == "active" else "❌"
                return f"{status_emoji} Статус каналу {channel_name} змінено на {new_status}"
            else:
                return f"❌ Поми��ка зміни статусу каналу {channel_name}"
                
        except Exception as e:
            logger.error(f"Помилка зміни статусу каналу {channel_name}: {e}")
            return f"❌ Помилка зміни статусу каналу: {str(e)}"

    def register_handlers(self):
        """Реєстрація обробників подій"""
        try:
            # Обробник команд бота
            @self.bot_client.on(events.NewMessage(pattern='/start'))
            async def start_handler(event):
                """Обробка команди /start"""
                try:
                    await event.respond(
                        "🤖 Привет! Я вторговий бот.\n\n"
                        "Оберіть опцію з меню нижче:",
                        buttons=[
                            [Button.inline("💰 Баланс і позиції", b"balance_positions")],
                            [Button.inline("📊 Активні ордери", b"active_orders")],
                            [Button.inline("📡 Керування каналами", b"channels_settings")],
                            [Button.inline("📈 Статистика", b"statistics")],
                            [Button.inline("⚙️ Налаштування", b"settings")]
                        ]
                    )
                    await self.send_log(f"👤 Користувач {event.sender_id} розпочав роботу з ботом")
                except Exception as e:
                    logger.error(f"Помилка обробки команди /start: {e}", exc_info=True)
                    await event.respond("❌ Помилка: Не вдалося відобразити меню")
                    await self.send_log(f"❌ Помилка запуску бота для користувача {event.sender_id}: {str(e)}")
            
            # Обробник кнопок
            @self.bot_client.on(events.CallbackQuery())
            async def callback_handler(event):
                """Обробка натискань кнопок"""
                try:
                    data = event.data.decode()
                    
                    # Логуємо натискання кнопки
                    logger.info(f"Користувач {event.sender_id} натиснув кнопку: {data}")
                    await self.send_log(f"👆 Користувач {event.sender_id} обрав опцію: {data}")
                    
                    # Обробляємо натискання з повторними спробами
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            await self.handle_callback(event, data)
                            await event.answer()  # Підтверджуємо обробку callback
                            break
                        except Exception as e:
                            if attempt == max_retries - 1:
                                logger.error(f"Помилка обробки callback після {max_retries} спроб: {e}")
                                await event.answer("❌ Помилка обробки запиту", alert=True)
                                await self.send_log(f"❌ Помилка обробки callback для користувача {event.sender_id}: {str(e)}")
                        else:
                                await asyncio.sleep(1)  # Чекаємо перед повторною спробою
                    
                except Exception as e:
                    logger.error(f"Помилка обробки callback: {e}")
                    try:
                        await event.answer("❌ Помилка: Не вдалося обробити дію", alert=True)
                    except:
                        pass
                    await self.send_log(f"❌ Помилка обробки callback для користувача {event.sender_id}: {str(e)}")
            
            # Обробник повідомлень з каналів моніторингу
            @self.monitor_client.on(events.NewMessage())
            async def monitor_message_handler(event):
                """Обробка повідомлень з каналів моніторингу"""
                try:
                    # Отримуємо канал
                    channel = await event.get_chat()
                    channel_name = f"@{channel.username}" if channel.username else str(channel.id)
                    
                    # Ігноруємо повідомлення з каналу логів
                    monitor_channel = os.getenv('MONITOR_CHANNEL_ID')
                    if monitor_channel:
                        if (channel_name == monitor_channel or 
                            str(channel.id) == monitor_channel or 
                            channel_name == "@botlogs7777"):
                            return
                    
                    logger.info(f"Отримано повідомлення з каналу {channel_name}")
                    logger.debug(f"Текст повідомлення: {event.message.text}")
                    
                    # Перевіряємо чи канал активний
                    db_channel = self.db.get_channel_by_name(channel_name)
                    if not db_channel:
                        logger.warning(f"Канал {channel_name} не знайдено в базі даних")
                        return
                        
                    if db_channel['status'] != 'active':
                        logger.warning(f"Канал {channel_name} неактивний")
                        return
                    
                    # Парсимо повідомлення
                    parser = MessageParser()
                    signal = parser.parse(event.message.text)
                    
                    if signal:
                        logger.info(f"Розпізнано сигнал: {signal}")
                        
                        # Логуємо отримання сигналу
                        log_message = [
                            "🎯 НОВИЙ СИГНАЛ",
                            f"• Канал: {channel_name}",
                            f"• Токен: {signal.get('token_name', 'Unknown')}",
                            f"• Адреса: {signal.get('token_address', 'Unknown')}",
                            f"• Тип: {signal.get('signal_type', 'Unknown')}",
                            "➖➖➖➖➖➖➖➖➖➖"
                        ]
                        await self.send_log("\n".join(log_message))
                        
                        # Перевіряємо необхідні поля
                        if not signal.get('token_address'):
                            log_message = [
                                "❌ ПОМИЛКА СИГНАЛУ",
                                "• Причина: Відсутня адреса токена",
                                "➖➖➖➖➖➖➖➖➖➖"
                            ]
                            await self.send_log("\n".join(log_message))
                            return
                            
                        # Додаємо сигнал в базу даних
                        signal_data = {
                            'message_id': event.message.id,
                            'channel_id': channel.id,
                            'token_address': signal['token_address'],
                            'token_name': signal.get('token_name', 'Unknown'),
                            'signal_type': signal.get('signal_type', 'unknown'),
                            'price': signal.get('price', 0),
                            'amount': signal.get('amount', 0),
                            'timestamp': datetime.now(),
                            'status': 'received'
                        }
                        self.db.add_signal(signal_data)
                        
                        # Передаємо сигнал на обробку
                        await self.trading_executor.handle_trade_signal(signal)
                        
                    else:
                        logger.debug(f"Повідомлення не містить торгового сигналу")
                        
                except Exception as e:
                    logger.error(f"Помилка обробки повідомлення: {e}")
                    await self.send_log(f"❌ Помилка обробки повідомлення: {str(e)}")
            
            logger.info("Обробники подій зареєстровано")
            
        except Exception as e:
            logger.error(f"Помилка реєстрації обробників: {e}", exc_info=True)
            raise

    def setup_logging(self):
        """Налаштування логування"""
        try:
            # Створюємо директорію для логів якщо її немає
            if not os.path.exists('logs'):
                os.makedirs('logs')
                
            # Вдаляємо стандартний обробник
            logger.remove()
            
            # Додаємо обробник для файлу
            logger.add(
                'logs/bot.log',
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                rotation="1 day",
                retention="7 days",
                level=20  # INFO
            )
            
            # Додаємо обробник для консолі
            logger.add(
                sys.stdout,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                level=20  # INFO
            )
            
            # Налаштовуємо рівні логування для інших модулів
            logging.getLogger('telethon').setLevel(logging.WARNING)
            logging.getLogger('asyncio').setLevel(logging.WARNING)
            
            logger.info("Логування налаштовано")
            
        except Exception as e:
            print(f"Помилка налаштування логування: {e}")
            raise

    async def handle_callback(self, event, data):
        """Обробка callback-ів від кнопок"""
        try:
            if data == "add_channel":
                # Змінюємо стан на очікування введення назви каналу
                await event.respond(
                    "Введіть назву каналу у форматі @channel_name:",
                    buttons=[[Button.inline("⬅️ Назад", b"manage_channels")]]
                )
                return
                    
            if data == "main_menu":
                await event.respond(
                    "🤖 Головне меню:",
                    buttons=[
                        [Button.inline("💰 Баланс і позиції", b"balance_positions")],
                        [Button.inline("📊 Активні ордери", b"active_orders")],
                        [Button.inline("📡 Керування каналами", b"manage_channels")],
                        [Button.inline("📈 Статистика", b"statistics")],
                        [Button.inline("⚙️ Налаштування", b"settings")]
                    ]
                )
                
            elif data == "balance_positions":
                # Отримуємо баланс
                balance = await self.trading_executor.get_balance()
                if balance and isinstance(balance, dict):
                    # Формуємо повідомлення
                    message = [
                        "💰 Баланс і позиції:\n",
                        f"• SOL: {balance.get('sol_balance', 0):.4f}",
                        f"• Загальна вартість: {balance.get('total_value', 0):.4f} SOL",
                        "\n📊 Токени на балансі:"
                    ]
                    
                    if 'tokens' in balance and balance['tokens']:
                        for token in balance['tokens']:
                            message.append(
                                f"\n• {token['symbol']} ({token['name']}):"
                                f"\n  └ Баланс: {token['balance']:.6f}"
                                f"\n  └ Ціна: {token['price']:.6f} SOL"
                                f"\n  └ Вартість: {token['value']:.4f} SOL"
                            )
                    else:
                        message.append("\nНмає токенів на балансі")
                    
                    await event.edit(
                        "\n".join(message),
                        buttons=[[Button.inline("⬅️ Назад", b"main_menu")]]
                    )
                else:
                    await event.edit(
                        "❌ Помилка отримання балансу",
                        buttons=[[Button.inline("⬅️ Назад", b"main_menu")]]
                    )
                    
            elif data == "active_orders":
                # Отримуємо активні ордери
                orders = self.db.get_active_orders()
                
                # Формуємо повідомлення
                message = ["📊 Активні ордери:"]
                
                if orders:
                    for order in orders:
                        message.append(
                            f"\n• Ордер #{order['id']}:"
                            f"\n  └ Тип: {order['type']}"
                            f"\n  └ Ціна: {order['price']:.6f} SOL"
                            f"\n  └ Кількість: {order['amount']:.6f}"
                            f"\n  └ ��татус: {order['status']}"
                        )
                else:
                    message.append("\nНемає активних ордерів")
                    
                await event.edit(
                    "\n".join(message),
                    buttons=[[Button.inline("⬅️ Назад", b"main_menu")]]
                )
                
            elif data == "manage_channels":
                await self.manage_channels(event)
                
            elif data == "statistics":
                # Отримуємо статистику
                stats = self.db.get_trading_stats()
                
                # Отримуємо сигнали за сьогодні
                today_signals = self.db.get_signals_in_time_range(
                    datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
                    datetime.now()
                )
                
                # Отримуємо транзакції за сьогодні
                today_transactions = self.db.get_transactions_in_time_range(
                    datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
                    datetime.now()
                )
                
                message = ["📈 Статистика торгівлі\n"]
                
                if stats and isinstance(stats, dict):
                    message.extend([
                        "💰 Загальна статистика:",
                        f"• Всього угод: {stats.get('total_trades', 0)}",
                        f"• Прибуткових: {stats.get('profitable_trades', 0)}",
                        f"• Збиткових: {stats.get('unprofitable_trades', 0)}",
                        f"• Вінрейт: {stats.get('win_rate', 0):.2f}%",
                        f"• Загальний P&L: {stats.get('total_pnl', 0):.4f} SOL",
                        f"• Середній P&L: {stats.get('avg_pnl', 0):.4f} SOL",
                        f"• Максимальний профіт: {stats.get('max_profit', 0):.4f} SOL",
                        f"• Максимальний збиток: {stats.get('max_loss', 0):.4f} SOL",
                        f"• Торгується токенів: {stats.get('traded_tokens', 0)}",
                        f"• Загальний об'єм: {stats.get('total_volume', 0):.4f} SOL\n"
                    ])
                else:
                    message.append("Загальна статистика відсутня\n")
                    
                message.extend([
                    "📅 Сьогодні:",
                    f"• Отримано сигналів: {len(today_signals)}",
                    f"• Виконано транзакцій: {len(today_transactions)}"
                ])
                
                buttons = [
                    [Button.inline("📊 Детальна статистика", b"detailed_stats")],
                    [Button.inline("⬅️ Назад", b"main_menu")]
                ]
                
                await event.edit("\n".join(message), buttons=buttons)
                
            elif data == "detailed_stats":
                # Отримуємо статистику по токенах
                tokens = self.db.get_trades_by_token(None)  # None для отримання всіх токенів
                
                message = ["📊 Статистика по токенах:\n"]
                
                if tokens:
                    for token in tokens:
                        stats = self.db.get_token_stats(token['token_address'])
                        if stats:
                            message.append(
                                f"• {token['token_name']}:"
                                f"\n  └ Угод: {stats.get('total_trades', 0)}"
                                f"\n  └ Вінрейт: {stats.get('win_rate', 0):.2f}%"
                                f"\n  └ P&L: {stats.get('total_pnl', 0):.4f} SOL"
                                f"\n  └ Об'єм: {stats.get('total_volume', 0):.4f} SOL"
                            )
                else:
                    message.append("Немає даних для відображення")
                    
                await event.edit(
                    "\n".join(message),
                    buttons=[[Button.inline("⬅️ Назад", b"statistics")]]
                )
                
            elif data == "settings":
                await event.edit(
                    "⚙️ Налаштування:\n\n"
                    "Виберіть категорію налаштувань:",
                    buttons=[
                        [Button.inline("📡 Керування каналами", b"channels_settings")],
                        [Button.inline("💰 Торгові параметри", b"trade_settings")],
                        [Button.inline("⚠️ Ризик-менеджмент", b"risk_settings")],
                        [Button.inline("⬅️ Назад", b"main_menu")]
                    ]
                )
                
            elif data == "channels_settings":
                # Отримуємо список каналів
                channels = self.db.get_channels()
                message = ["📡 Керування каналами:\n"]
                
                if channels:
                    for channel in channels:
                        status = "✅ Активний" if channel["status"] == "active" else "❌ Неактивний"
                        message.append(f"{channel['name']}: {status}")
                else:
                    message.append("Немає доданих каналів")
                    
                buttons = []
                for channel in channels:
                    buttons.append([
                        Button.inline(
                            f"{'🔴 Деактивувати' if channel['status'] == 'active' else '🟢 Активувати'} {channel['name']}", 
                            f"toggle_channel:{channel['name']}".encode()
                        )
                    ])
                    
                buttons.append([Button.inline("➕ Додати канал", b"add_channel")])
                buttons.append([Button.inline("⬅️ Назад", b"settings")])
                
                await event.edit("\n".join(message), buttons=buttons)
                
            elif data == "trade_settings":
                # Отримуємо поточні налаштування
                settings = self.db.get_settings()
                
                message = [
                    "💰 Торгові параметри:\n",
                    f"• Мінімальний баланс SOL: {settings.get('min_sol_balance', 0.02)}",
                    f"• Розмір позиції: {settings.get('position_size', 5)}%",
                    f"• Максимальний slippage: {settings.get('max_slippage', 1)}%"
                ]
                
                buttons = [
                    [Button.inline("Змінити мін. баланс", b"edit_min_balance")],
                    [Button.inline("Змінити розмір позиції", b"edit_position_size")],
                    [Button.inline("Змінити макс. slippage", b"edit_max_slippage")],
                    [Button.inline("⬅️ Назад", b"settings")]
                ]
                
                await event.edit("\n".join(message), buttons=buttons)
                
            elif data == "risk_settings":
                # Отримуємо поточні налаштування
                settings = self.db.get_settings()
                
                message = [
                    "⚠️ Налаштування ризиків:\n",
                    "📈 Take-profit рівні:",
                    f"• 100% прибутку - продаж {settings.get('tp_1_percent', 20)}%",
                    f"• 250% прибутку - продаж {settings.get('tp_2_percent', 20)}%",
                    f"• 500% прибутку - продаж {settings.get('tp_3_percent', 20)}%",
                    f"\n📉 Stop-loss:",
                    f"• Рівень: {settings.get('stop_loss_level', -75)}%"
                ]
                
                buttons = [
                    [Button.inline("Змінити take-profit", b"edit_tp_levels")],
                    [Button.inline("Змінити stop-loss", b"edit_sl_level")],
                    [Button.inline("⬅️ Назад", b"settings")]
                ]
                
                await event.edit("\n".join(message), buttons=buttons)
                
            elif data.startswith("add_channel:"):
                channel_name = data.split(":")[1]
                result = await self.add_channel(channel_name)
                await event.edit(result, buttons=[[Button.inline("⬅️ Назад", b"manage_channels")]])
                
            elif data.startswith("remove_channel:"):
                channel_name = data.split(":")[1]
                result = await self.remove_channel(channel_name)
                await event.edit(result, buttons=[[Button.inline("⬅️ Назад", b"manage_channels")]])
                
            elif data.startswith("toggle_channel:"):
                channel_name = data.split(":")[1]
                channel = self.db.get_channel(channel_name)
                
                if channel:
                    new_status = "inactive" if channel["status"] == "active" else "active"
                    self.db.update_channel_status(channel_name, new_status)
                    
                    # Оновлюємо список каналів
                    channels = self.db.get_channels()
                    message = ["📡 Керування каналами:\n"]
                    
                    for ch in channels:
                        status = "✅ Активний" if ch["status"] == "active" else "❌ Неактивний"
                        message.append(f"{ch['name']}: {status}")
                        
                    buttons = []
                    for ch in channels:
                        buttons.append([
                            Button.inline(
                                f"{'🔴 Деактивувати' if ch['status'] == 'active' else '🟢 Активувати'} {ch['name']}", 
                                f"toggle_channel:{ch['name']}".encode()
                            )
                        ])
                    
                    buttons.append([Button.inline("➕ Додати канал", b"add_channel")])
                    buttons.append([Button.inline("⬅️ Назад", b"settings")])
                    
                    await event.edit(
                        f"{'✅ Канал активовано' if new_status == 'active' else '❌ Канал деактивовано'}\n\n" + "\n".join(message),
                        buttons=buttons
                    )
                
            elif data.startswith("edit_"):
                setting = data.replace("edit_", "")
                
                if setting == "min_balance":
                    await event.edit(
                        "💰 Введіть новий мінімальний баланс SOL (наприклад: 0.02):",
                        buttons=[[Button.inline("⬅️ Назад", b"trade_settings")]]
                    )
                    self.waiting_for[event.sender_id] = ("min_balance", None)
                    
                elif setting == "position_size":
                    await event.edit(
                        "💰 Введіть новий розмір позиції у відсотках (наприклад: 5):",
                        buttons=[[Button.inline("⬅️ Назад", b"trade_settings")]]
                    )
                    self.waiting_for[event.sender_id] = ("position_size", None)
                    
                elif setting == "max_slippage":
                    await event.edit(
                        "💰 Введіть новий максимальний slippage у відсотках (наприклад: 1):",
                        buttons=[[Button.inline("⬅️ Назад", b"trade_settings")]]
                    )
                    self.waiting_for[event.sender_id] = ("max_slippage", None)
                    
                elif setting == "tp_levels":
                    await event.edit(
                        "📈 Введіть нові рівні take-profit через кому (наприклад: 20,20,20):",
                        buttons=[[Button.inline("⬅️ Назад", b"risk_settings")]]
                    )
                    self.waiting_for[event.sender_id] = ("tp_levels", None)
                    
                elif setting == "sl_level":
                    await event.edit(
                        "📉 Введіть новий рівень stop-loss у відсотках (наприклад: -75):",
                        buttons=[[Button.inline("⬅️ Назад", b"risk_settings")]]
                    )
                    self.waiting_for[event.sender_id] = ("sl_level", None)
                    
            # Обробка введених значень
            elif event.sender_id in self.waiting_for:
                setting_type, _ = self.waiting_for[event.sender_id]
                value = event.text.strip()
                
                try:
                    if setting_type == "min_balance":
                        value = float(value)
                        if value <= 0:
                            raise ValueError("Значення має бути більше 0")
                        self.db.update_setting("min_sol_balance", str(value))
                        
                    elif setting_type == "position_size":
                        value = float(value)
                        if not 0 < value <= 100:
                            raise ValueError("Значення має бути від 1 до 100")
                        self.db.update_setting("position_size", str(value))
                        
                    elif setting_type == "max_slippage":
                        value = float(value)
                        if not 0 < value <= 100:
                            raise ValueError("З��ачення має бути від 1 до 100")
                        self.db.update_setting("max_slippage", str(value))
                        
                    elif setting_type == "tp_levels":
                        levels = [float(x.strip()) for x in value.split(",")]
                        if len(levels) != 3:
                            raise ValueError("Потрібно вказати 3 значення")
                        if not all(0 <= x <= 100 for x in levels):
                            raise ValueError("Значення мають бути від 0 до 100")
                        self.db.update_setting("tp_1_percent", str(levels[0]))
                        self.db.update_setting("tp_2_percent", str(levels[1]))
                        self.db.update_setting("tp_3_percent", str(levels[2]))
                        
                    elif setting_type == "sl_level":
                        value = float(value)
                        if not -100 < value < 0:
                            raise ValueError("Значення має бути від -100 до 0")
                        self.db.update_setting("stop_loss_level", str(value))
                        
                    # Повертаємо до відповідного меню
                    if setting_type in ["min_balance", "position_size", "max_slippage"]:
                        await self.handle_callback(event, "trade_settings")
                    else:
                        await self.handle_callback(event, "risk_settings")
                        
                except ValueError as e:
                    await event.respond(f"❌ Помилка: {str(e)}")
                except Exception as e:
                    await event.respond("❌ Помилка: Неправильний формат значення")
                    
                # Очищаємо стан очікування
                del self.waiting_for[event.sender_id]
                
        except Exception as e:
            logger.error(f"Помилка обробки callback: {e}")
            await event.edit(
                f"❌ Помилка: {str(e)}",
                buttons=[[Button.inline("⬅️ Назад", b"main_menu")]]
            )
            
    async def handle_new_message(self, event):
        """Обробка нових повідомлень"""
        try:
            # Отримуємо канал
            channel = await event.get_chat()
            
            # Перевіряємо чи це активний канал
            db_channel = self.db.get_channel_by_name(f"@{channel.username}")
            if not db_channel or db_channel["status"] != "active":
                return
                
            # Парсимо повідомлення
            signal = self.message_parser.parse(event.message.text)
            if signal:
                # Додаємо сигнал в базу даних
                signal_data = {
                    "message_id": event.message.id,
                    "channel_id": channel.id,
                    "token_address": signal.token_address,
                    "token_name": signal.token_name,
                    "signal_type": signal.signal_type,
                    "price": signal.price,
                    "amount": signal.amount
                }
                self.db.add_signal(signal_data)
                
                # Обробляємо сигнал
                await self.trading_executor.handle_trade_signal(signal)
                
        except Exception as e:
            logger.error(f"Помилка обробки повідомлення: {e}")
            await self.send_log(f"❌ Помилка обробки повідомлення: {str(e)}")

    async def setup_default_channels(self):
        """Налаштування каналів за замовчуванням"""
        try:
            # Додаємо канал для логів
            monitor_channel_id = os.getenv('MONITOR_CHANNEL_ID')
            if monitor_channel_id:
                monitor_channel_id = int(monitor_channel_id)
                self.monitor_channel = monitor_channel_id
                channel_data = {
                    'name': 'monitor_channel',
                    'type': 'monitor',
                    'status': 'active'
                }
                self.db.add_channel(channel_data)
                logger.info("Канал логів додано до бази даних")
                logger.info(f"Встановлено канал логування: {monitor_channel_id}")
                
            # Додаємо канали для моніторингу
            source_channels = json.loads(os.getenv('SOURCE_CHANNELS', '[]'))
            added_count = 0
            
            for channel_name in source_channels:
                channel_data = {
                    'name': channel_name,
                    'type': 'source',
                    'status': 'active'
                }
                self.db.add_channel(channel_data)
                added_count += 1
                
            logger.info(f"Додано {added_count} каналів за замовчуванням")
            
        except Exception as e:
            logger.error(f"Помилка налаштування каналів за замовчуванням: {e}")

    async def handle_trade_signal(self, signal):
        """Обробка торгового сигналу"""
        try:
            logger.info(f"Отримано сигнал: {signal}")
            await self.send_log("🔄 Обробка торгового сигналу...")
            
            # Перевіряємо баланс
            balance = await self.get_balance_with_retry()
            if not balance or balance['sol_balance'] < MIN_SOL_BALANCE:
                await self.send_log(f"❌ Недостатньо балансу: {balance['sol_balance']} SOL")
                return
            
            # Перевіряємо токен
            if not await self.verify_token_with_retry(signal['token_address']):
                await self.send_log("❌ Токен не існує або не є SPL токеном")
                return
            
            # Отримуємо інформацію про токен
            token_info = await self.get_token_info(signal['token_address'])
            signal['token_name'] = token_info['name']
            signal['token_symbol'] = token_info['symbol']
            
            logger.info(f"Інформація по токен: {token_info}")
            await self.send_log(f"ℹ️ Інформація про токен:\n• Назва: {token_info['name']}\n• Символ: {token_info['symbol']}")
            
            # Розраховуємо суму для покупки (5% від балансу SOL)
            purchase_amount = balance['sol_balance'] * Decimal('0.05')
            
            # Отримуємо котирування
            logger.info(f"Запит котирування для {purchase_amount} SOL")
            await self.send_log(f"💱 Запит котирування для {purchase_amount:.4f} SOL")
            
            quote = await self.jupiter.get_quote(
                signal['token_address'],
                float(purchase_amount),
                slippage=1  # 1% slippage
            )
            
            if not quote:
                await self.send_log("❌ Не вдалося отримати котирування")
                return
            
            logger.info(f"Отримано котирування: {quote}")
            await self.send_log(f"📊 Отримано котирування:\n• Ціна: {quote['price']:.6f} SOL\n• Кількість: {quote['out_amount']:.6f}")
            
            # Викону��мо своп
            tx = await self.jupiter.swap(quote)
            if not tx:
                await self.send_log("❌ Не вдалося виконати своп")
                return
            
            logger.info(f"Транзакція відправлена: {tx['signature']}")
            await self.send_log(f"📤 Транзакція відправлена: {tx['signature']}")
            
            # Додаємо транзакцію в базу даних
            self.db.add_transaction({
                'signature': tx['signature'],
                'token_address': signal['token_address'],
                'amount': quote['out_amount'],
                'type': 'buy',
                'status': 'pending',
                'balance_change': -float(purchase_amount)
            })
            
            # Чекаємо підтвердження
            status = await self.wait_for_transaction_confirmation(tx['signature'])
            logger.info(f"Статус транзакції: {status}")
            await self.send_log(f"📝 Статус транзакції: {status}")
            
            # Оновлюємо статус транзакції
            self.db.update_transaction(tx['signature'], {
                'status': status,
                'confirmations': tx.get('confirmations', 0)
            })
            
            if status == 'confirmed':
                # Додаємо позицію
                position_data = {
                    'token_address': signal['token_address'],
                    'token_symbol': signal['token_symbol'],
                    'entry_price': quote['price'],
                    'current_price': quote['price'],
                    'amount': quote['out_amount'],
                    'remaining_amount': quote['out_amount'],
                    'status': 'open',
                    'transaction_signature': tx['signature']
                }
                position_id = self.db.add_position(position_data)
                
                # Додаємо торгову операцію
                trade_data = {
                    'token_address': signal['token_address'],
                    'token_name': signal['token_name'],
                    'entry_price': quote['price'],
                    'amount': quote['out_amount'],
                    'type': 'buy',
                    'status': 'open',
                    'position_id': position_id
                }
                self.db.add_trade(trade_data)
                
                # Оновлюємо метрики
                self.update_performance_metrics(True, time.time())
                
                await self.send_log(
                    f"✅ Успішна покупка:\n"
                    f"• Токен: {signal['token_name']} ({signal['token_symbol']})\n"
                    f"• Витрачено: {purchase_amount:.4f} SOL\n"
                    f"• Отримано: {quote['out_amount']:.6f} токенів\n"
                    f"• Ціна: {quote['price']:.6f} SOL\n"
                    f"• Транзакція: https://solscan.io/tx/{tx['signature']}"
                )
                
            else:
                # Оновлюємо метрики при невдачі
                self.update_performance_metrics(False, time.time())
                await self.send_log(f"❌ Помилка транзакції: {status}")
            
        except Exception as e:
            logger.error(f"Помилка обробки сигналу: {e}", exc_info=True)
            await self.send_log(f"❌ Помилка: {str(e)}")
            self.db.add_log({
                'level': 'ERROR',
                'message': f"Помилка обробки сигналу для {signal.get('token_name', 'Unknown')}",
                'details': str(e),
                'session_id': self.current_session_id
            })

    async def show_balance_positions(self, event):
        """Відображення балансу і позицій"""
        try:
            await self.send_log(f"💰 Запит балансу від користувача {event.sender_id}")
            
            # Отримуємо баланс всіх позицій
            balance_data = await self.trading_executor.get_positions_balance()
            
            message = ["💰 Баланс і позиції:\n"]
            message.append(f"💎 Загальний баланс: {balance_data['total_balance_sol']:.4f} SOL\n")
            
            if balance_data['positions']:
                message.append("📊 Відкриті позиції:")
                for pos in balance_data['positions']:
                    message.append(
                        f"\n• {pos['token_name']} ({pos['token_address'][:8]}...):"
                        f"\n  Кількість: {pos['amount']:.4f}"
                        f"\n  Ціна: {pos['current_price']:.8f} SOL"
                        f"\n  Вартість: {pos['value_sol']:.4f} SOL"
                    )
            else:
                message.append("\n📭 Нмає відкритих позицій")
            
            await event.edit("\n".join(message), buttons=[
                [Button.inline("🔄 Оновити", b"balance_positions")],
                [Button.inline("⬅️ Назад", b"main_menu")]
            ])
            
            await self.send_log(f"✅ Баланс успішно відображено для користувача {event.sender_id}")
            
        except Exception as e:
            logger.error(f"Помилка відображення балансу: {str(e)}")
            await event.edit("❌ Помилка отримання балансу", buttons=[
                [Button.inline("🔄 Спробувати ще раз", b"balance_positions")],
                [Button.inline("⬅️ Назад", b"main_menu")]
            ])
            await self.send_log(f"❌ Помилка відображення балансу для користувача {event.sender_id}: {str(e)}")

    async def send_log(self, message: str):
        """Відправка повідомлення в канал логів"""
        try:
            if self.monitor_channel:
                await self.bot_client.send_message(self.monitor_channel, message)
        except Exception as e:
            logger.error(f"Помилка в��дправки логу: {e}")

async def main():
    """Головна функція запуску бота"""
    try:
        # Завантажуємо змінні оточноння
        load_dotenv()
        
        # Отримуємо необхідні параметри
        api_id = int(os.getenv('API_ID'))
        api_hash = os.getenv('API_HASH')
        bot_token = os.getenv('BOT_TOKEN')
        
        # Створюємо екземпляр бота
        bot = TradingBot(api_id, api_hash, bot_token)
        
        # Запускаємо бота
        await bot.start()
        
    except Exception as e:
        logger.error(f"Помилка запуску бота: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    # Налаштовуємо логування
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Запускаємо бот
    asyncio.run(main())