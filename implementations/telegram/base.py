from typing import Dict, Any, Optional, Callable, List
import asyncio
from datetime import datetime
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from interfaces.telegram_interfaces import BaseTelegramInterface

class BaseTelegramImplementation(BaseTelegramInterface):
    """Базова імплементація для Telegram ботів"""
    
    def __init__(self):
        """Ініціалізація базового бота"""
        self.config = {}
        self.bot = None
        self.application = None
        self.commands = {}
        self.message_handlers = []
        self.error_handlers = []
        
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Ініціалізація бота"""
        try:
            self.config = config
            
            # Створюємо бота
            self.bot = Bot(token=config['telegram_token'])
            
            # Налаштовуємо застосунок
            self.application = Application.builder().token(config['telegram_token']).build()
            
            # Реєструємо базові команди
            self._register_base_commands()
            
            return True
            
        except Exception as e:
            print(f"Error initializing Telegram bot: {e}")
            return False
            
    async def start(self) -> bool:
        """Запуск бота"""
        try:
            if not self.application:
                return False
                
            # Запускаємо бота
            await self.application.initialize()
            await self.application.start()
            await self.application.run_polling()
            
            return True
            
        except Exception as e:
            print(f"Error starting Telegram bot: {e}")
            return False
            
    async def stop(self) -> bool:
        """Зупинка бота"""
        try:
            if self.application:
                await self.application.stop()
                await self.application.shutdown()
            return True
            
        except Exception as e:
            print(f"Error stopping Telegram bot: {e}")
            return False
            
    def add_command(self, command: str, handler: Callable, description: str) -> None:
        """Додавання нової команди"""
        try:
            # Зберігаємо інформацію про команду
            self.commands[command] = {
                'handler': handler,
                'description': description
            }
            
            # Реєструємо обробник команди
            self.application.add_handler(
                CommandHandler(command, handler)
            )
            
        except Exception as e:
            print(f"Error adding command: {e}")
            
    def add_message_handler(self, handler: Callable) -> None:
        """Додавання обробника повідомлень"""
        try:
            # Зберігаємо обробник
            self.message_handlers.append(handler)
            
            # Реєструємо обробник повідомлень
            self.application.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, handler)
            )
            
        except Exception as e:
            print(f"Error adding message handler: {e}")
            
    def add_error_handler(self, handler: Callable) -> None:
        """Додавання обробника помилок"""
        try:
            # Зберігаємо обробник
            self.error_handlers.append(handler)
            
            # Реєструємо обробник помилок
            self.application.add_error_handler(handler)
            
        except Exception as e:
            print(f"Error adding error handler: {e}")
            
    async def send_message(self, chat_id: int, text: str,
                          parse_mode: Optional[str] = None) -> bool:
        """Відправка повідомлення"""
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode
            )
            return True
            
        except Exception as e:
            print(f"Error sending message: {e}")
            return False
            
    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обробник команди /start"""
        try:
            welcome_message = (
                "👋 Вітаю! Я бот для торгівлі на Solana.\n\n"
                "Доступні команди:\n"
            )
            
            for command, info in self.commands.items():
                welcome_message += f"/{command} - {info['description']}\n"
                
            await update.message.reply_text(welcome_message)
            
        except Exception as e:
            print(f"Error handling start command: {e}")
            
    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обробник команди /help"""
        try:
            help_message = "📚 Список доступних команд:\n\n"
            
            for command, info in self.commands.items():
                help_message += f"/{command} - {info['description']}\n"
                
            await update.message.reply_text(help_message)
            
        except Exception as e:
            print(f"Error handling help command: {e}")
            
    def _register_base_commands(self) -> None:
        """Реєстрація базових команд"""
        self.add_command('start', self._start_command, 'Почати роботу з ботом')
        self.add_command('help', self._help_command, 'Показати список команд') 