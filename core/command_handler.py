"""Обробник команд бота"""

from typing import Optional, Dict, Any
import asyncio
from datetime import datetime
from telethon import TelegramClient, events
from telethon.tl.types import Message

from utils import get_logger, measure_time
from utils.decorators import admin_only, log_execution
from .notification_manager import NotificationManager
from .config_manager import ConfigManager
from .repository_factory import RepositoryFactory

logger = get_logger("command_handler")

class CommandHandler:
    def __init__(
        self,
        notification_manager: NotificationManager,
        bot_client: TelegramClient,
        db_file: str = 'trading_bot.db'
    ):
        """
        Ініціалізація обробника команд
        
        Args:
            notification_manager: Менеджер сповіщень
            bot_client: Клієнт для взаємодії з адміністратором
            db_file: Шлях до файлу бази даних
        """
        self.notification_manager = notification_manager
        self.bot_client = bot_client
        self.config = ConfigManager()
        self._shutdown_flag = False
        
        # Ініціалізуємо репозиторії
        self.repos = RepositoryFactory(db_file)
        
    async def start_handling(self):
        """Запуск обробки команд"""
        try:
            # Реєструємо обробник команд
            @self.bot_client.on(events.NewMessage(pattern=r'/[a-zA-Z]+'))
            async def command_handler(event):
                if self._shutdown_flag:
                    return
                    
                try:
                    # Перевіряємо чи повідомлення від адміністратора
                    if not await self._is_admin(event.sender_id):
                        await event.reply("⛔️ У вас немає прав для виконання цієї команди")
                        return
                        
                    # Обробляємо команду
                    await self._process_command(event)
                    
                except Exception as e:
                    logger.error(f"Помилка обробки команди: {e}")
                    await self.notification_manager.send_error_notification(
                        str(e),
                        "CommandProcessingError"
                    )
            
            logger.info("Обробка команд запущена")
            
        except Exception as e:
            logger.error(f"Помилка запуску обробки команд: {e}")
            await self.notification_manager.send_error_notification(
                str(e),
                "CommandHandlingStartError"
            )
            raise
            
    async def stop_handling(self):
        """Зупинка обробки команд"""
        self._shutdown_flag = True
        self.repos.close_all()
        logger.info("Обробка команд зупинена")
        
    @admin_only
    async def _process_command(self, event: Message):
        """
        Обробка команди
        
        Args:
            event: Подія нової команди
        """
        try:
            command = event.message.text.split()[0].lower()
            args = event.message.text.split()[1:]
            
            # Визначаємо обробник для команди
            handlers = {
                '/start': self._handle_start,
                '/help': self._handle_help,
                '/status': self._handle_status,
                '/balance': self._handle_balance,
                '/positions': self._handle_positions,
                '/channels': self._handle_channels,
                '/add_channel': self._handle_add_channel,
                '/remove_channel': self._handle_remove_channel,
                '/settings': self._handle_settings,
                '/update_setting': self._handle_update_setting,
                '/stop': self._handle_stop
            }
            
            handler = handlers.get(command)
            if not handler:
                await event.reply(f"❌ Невідома команда: {command}\nВикористайте /help для списку доступних команд")
                return
                
            # Викликаємо відповідний обробник
            await handler(event, args)
            
        except Exception as e:
            logger.error(f"Помилка обробки команди {command}: {e}")
            await event.reply("❌ Помилка виконання команди")
            await self.notification_manager.send_error_notification(
                str(e),
                "CommandExecutionError",
                {"command": command}
            )
            
    async def _is_admin(self, user_id: int) -> bool:
        """
        Перевірка чи користувач є адміністратором
        
        Args:
            user_id: ID користувача
            
        Returns:
            bool: Результат перевірки
        """
        admin_ids = self.config.get('ADMIN_IDS', [])
        return user_id in admin_ids
        
    @log_execution
    async def _handle_start(self, event: Message, args: list):
        """Обробка команди /start"""
        await event.reply(
            "👋 Вітаю! Я бот для автоматичної торгівлі на Solana.\n\n"
            "Використайте /help для отримання списку доступних команд."
        )
        
    @log_execution
    async def _handle_help(self, event: Message, args: list):
        """Обробка команди /help"""
        help_text = (
            "📋 Доступні команди:\n\n"
            "/start - Початок роботи\n"
            "/help - Список команд\n"
            "/status - Статус бота\n"
            "/balance - Баланс гаманця\n"
            "/positions - Активні позиції\n"
            "/channels - Список каналів\n"
            "/add_channel - Додати канал\n"
            "/remove_channel - Видалити канал\n"
            "/settings - Налаштування\n"
            "/update_setting - Оновити налаштування\n"
            "/stop - Зупинити бота"
        )
        await event.reply(help_text)
        
    @log_execution
    async def _handle_status(self, event: Message, args: list):
        """Обробка команди /status"""
        try:
            # Отримуємо статистику
            stats = self.repos.stats_repository.get_trading_stats()
            
            status_text = (
                "📊 Статус бота:\n\n"
                f"Активний час: {stats['uptime']}\n"
                f"Оброблено сигналів: {stats['signals_processed']}\n"
                f"Відкрито позицій: {stats['positions_opened']}\n"
                f"Закрито позицій: {stats['positions_closed']}\n"
                f"Прибуток: {stats['total_profit']} SOL\n"
                f"Win rate: {stats['win_rate']}%"
            )
            await event.reply(status_text)
            
        except Exception as e:
            logger.error(f"Помилка отримання статусу: {e}")
            await event.reply("❌ Помилка отримання статусу")
            
    @log_execution
    async def _handle_balance(self, event: Message, args: list):
        """Обробка команди /balance"""
        try:
            # Отримуємо баланс
            balance = self.repos.stats_repository.get_wallet_balance()
            
            balance_text = (
                "💰 Баланс гаманця:\n\n"
                f"SOL: {balance['sol']}\n"
                f"USDC: {balance['usdc']}\n"
                f"Загальна вартість: ${balance['total_usd']}"
            )
            await event.reply(balance_text)
            
        except Exception as e:
            logger.error(f"Помилка отримання балансу: {e}")
            await event.reply("❌ Помилка отримання балансу")
            
    @log_execution
    async def _handle_positions(self, event: Message, args: list):
        """Обробка команди /positions"""
        try:
            # Отримуємо активні позиції
            positions = self.repos.position_repository.get_open_positions()
            
            if not positions:
                await event.reply("📊 Немає активних позицій")
                return
                
            positions_text = "📊 Активні позиції:\n\n"
            for pos in positions:
                positions_text += (
                    f"ID: {pos['id']}\n"
                    f"Токен: {pos['token_symbol']}\n"
                    f"Тип: {pos['position_type']}\n"
                    f"Ціна входу: {pos['entry_price']}\n"
                    f"Поточна ціна: {pos['current_price']}\n"
                    f"P&L: {pos['pnl']}%\n\n"
                )
            await event.reply(positions_text)
            
        except Exception as e:
            logger.error(f"Помилка отримання позицій: {e}")
            await event.reply("❌ Помилка отримання позицій")
            
    @log_execution
    async def _handle_channels(self, event: Message, args: list):
        """Обробка команди /channels"""
        try:
            # Отримуємо список каналів
            channels = self.repos.channel_repository.get_all_channels()
            
            if not channels:
                await event.reply("📢 Немає підключених каналів")
                return
                
            channels_text = "📢 Підключені канали:\n\n"
            for channel in channels:
                channels_text += (
                    f"ID: {channel['id']}\n"
                    f"Назва: {channel['name']}\n"
                    f"Статус: {'🟢 Активний' if channel['is_active'] else '🔴 Неактивний'}\n\n"
                )
            await event.reply(channels_text)
            
        except Exception as e:
            logger.error(f"Помилка отримання каналів: {e}")
            await event.reply("❌ Помилка отримання каналів")
            
    @log_execution
    async def _handle_add_channel(self, event: Message, args: list):
        """Обробка команди /add_channel"""
        if not args:
            await event.reply("❌ Вкажіть назву каналу")
            return
            
        channel_name = args[0]
        try:
            # Додаємо канал
            self.repos.channel_repository.add_channel({
                'name': channel_name,
                'username': channel_name,
                'type': 'trading',
                'is_active': True
            })
            
            await event.reply(f"✅ Канал {channel_name} успішно додано")
            
        except Exception as e:
            logger.error(f"Помилка додавання каналу: {e}")
            await event.reply("❌ Помилка додавання каналу")
            
    @log_execution
    async def _handle_remove_channel(self, event: Message, args: list):
        """Обробка команди /remove_channel"""
        if not args:
            await event.reply("❌ Вкажіть ID каналу")
            return
            
        try:
            channel_id = int(args[0])
            # Видаляємо канал
            self.repos.channel_repository.delete_channel(channel_id)
            
            await event.reply(f"✅ Канал успішно видалено")
            
        except ValueError:
            await event.reply("❌ Невірний формат ID каналу")
        except Exception as e:
            logger.error(f"Помилка видалення каналу: {e}")
            await event.reply("❌ Помилка видалення каналу")
            
    @log_execution
    async def _handle_settings(self, event: Message, args: list):
        """Обробка команди /settings"""
        settings = self.config.all_config
        
        settings_text = "⚙️ Поточні налаштування:\n\n"
        for section, values in settings.items():
            settings_text += f"{section}:\n"
            for key, value in values.items():
                settings_text += f"  {key}: {value}\n"
            settings_text += "\n"
            
        await event.reply(settings_text)
        
    @log_execution
    async def _handle_update_setting(self, event: Message, args: list):
        """Обробка команди /update_setting"""
        if len(args) < 2:
            await event.reply("❌ Вкажіть ключ та значення налаштування")
            return
            
        key = args[0]
        value = args[1]
        
        try:
            self.config.set(key, value)
            await event.reply(f"✅ Налаштування {key} оновлено")
            
        except Exception as e:
            logger.error(f"Помилка оновлення налаштування: {e}")
            await event.reply("❌ Помилка оновлення налаштування")
            
    @log_execution
    async def _handle_stop(self, event: Message, args: list):
        """Обробка команди /stop"""
        await event.reply("🛑 Зупиняю бота...")
        self._shutdown_flag = True
