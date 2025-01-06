import asyncio
import logging
import platform
import psutil
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List, Dict, Any

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Bot tokens
MANAGEMENT_BOT_TOKEN = os.getenv('TELEGRAM_MANAGEMENT_BOT_TOKEN')
NOTIFICATION_BOT_TOKEN = os.getenv('TELEGRAM_NOTIFICATION_BOT_TOKEN')
MONITORING_BOT_TOKEN = os.getenv('TELEGRAM_MONITORING_BOT_TOKEN')
LOGGING_BOT_TOKEN = os.getenv('TELEGRAM_LOGGING_BOT_TOKEN')

# Chat IDs
ADMIN_CHAT_IDS: List[int] = [
    int(id_str) for id_str in 
    os.getenv('TELEGRAM_ADMIN_CHAT_IDS', '').split(',') 
    if id_str.strip()
]

NOTIFICATION_CHAT_IDS: List[int] = [
    int(id_str) for id_str in 
    os.getenv('TELEGRAM_NOTIFICATION_CHAT_IDS', '').split(',') 
    if id_str.strip()
]

MONITORING_CHAT_IDS: List[int] = [
    int(id_str) for id_str in 
    os.getenv('TELEGRAM_MONITORING_CHAT_IDS', '').split(',') 
    if id_str.strip()
]

LOGGING_CHAT_IDS: List[int] = [
    int(id_str) for id_str in 
    os.getenv('TELEGRAM_LOGGING_CHAT_IDS', '').split(',') 
    if id_str.strip()
]

# Settings
MONITORING_CHECK_INTERVAL = int(os.getenv('TELEGRAM_MONITORING_INTERVAL', '300'))
LOGGING_MIN_LEVEL = getattr(logging, os.getenv('TELEGRAM_LOGGING_MIN_LEVEL', 'INFO'))

class BaseService(ABC):
    """Base interface for all Telegram services"""
    
    @abstractmethod
    async def start(self) -> None:
        """Start the service"""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the service"""
        pass
    
    @abstractmethod
    async def send_message(self, chat_id: int, text: str) -> Optional[Message]:
        """Send message to specified chat"""
        pass

class ManagementBot(BaseService):
    """Main management bot for trading operations"""
    
    def __init__(self, token: str, admin_ids: list[int]):
        """Initialize bot with token and admin IDs"""
        self.bot = Bot(token=token)
        self.dp = Dispatcher(self.bot)
        self.admin_ids = admin_ids
        
        # Initialize trading components
        self.position_manager = None  # Will be initialized later
        self.trade_validator = None   # Will be initialized later
        self.price_calculator = None  # Will be initialized later
        
        self._setup_handlers()
    
    def _setup_handlers(self) -> None:
        """Setup message handlers"""
        # Admin commands
        self.dp.register_message_handler(
            self._handle_open_position,
            lambda msg: self._is_admin(msg.from_user.id),
            commands=['open']
        )
        self.dp.register_message_handler(
            self._handle_close_position,
            lambda msg: self._is_admin(msg.from_user.id),
            commands=['close']
        )
        self.dp.register_message_handler(
            self._handle_positions,
            lambda msg: self._is_admin(msg.from_user.id),
            commands=['positions']
        )
        
        # User commands
        self.dp.register_message_handler(
            self._handle_start,
            commands=['start', 'help']
        )
        self.dp.register_message_handler(
            self._handle_balance,
            commands=['balance']
        )
    
    def _is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in self.admin_ids
    
    async def _handle_start(self, message: Message) -> None:
        """Handle /start command"""
        help_text = (
            "🤖 Вітаю! Я бот для керування торгівлею.\n\n"
            "Доступні команди:\n"
            "/open TOKEN AMOUNT - Відкрити нову позицію\n"
            "/close ID - Закрити позицію\n"
            "/positions - Показати відкриті позиції\n"
            "/balance - Показати баланс\n"
            "/help - Показати це повідомлення\n\n"
            "❗️ Деякі команди доступні тільки для адміністраторів"
        )
        await message.reply(help_text)
    
    async def _handle_open_position(self, message: Message) -> None:
        """Handle /open command"""
        try:
            # Expected format: /open TOKEN AMOUNT
            _, token, amount = message.text.split()
            amount = float(amount)
            
            # Validate token
            if not await self.trade_validator.validate_token(token):
                await message.reply(f"❌ Помилка: Невідомий токен {token}")
                return
            
            # Get current price
            price = await self.price_calculator.get_price(token)
            if not price:
                await message.reply("❌ Помилка: Не вдалося отримати ціну")
                return
            
            # Open position
            position = await self.position_manager.open_position(token, amount, price)
            
            await message.reply(
                f"✅ Позицію відкрито:\n"
                f"ID: {position.id}\n"
                f"Токен: {position.token}\n"
                f"Кількість: {position.amount}\n"
                f"Ціна: {position.entry_price}"
            )
            
        except ValueError as e:
            await message.reply(f"❌ Помилка: {str(e)}")
        except Exception as e:
            await message.reply("❌ Сталася помилка при відкритті позиції")
    
    async def _handle_close_position(self, message: Message) -> None:
        """Handle /close command"""
        try:
            # Expected format: /close POSITION_ID
            _, position_id = message.text.split()
            position_id = int(position_id)
            
            # Close position
            position = await self.position_manager.close_position(position_id)
            
            await message.reply(
                f"✅ Позицію закрито:\n"
                f"ID: {position.id}\n"
                f"Прибуток: {position.profit}"
            )
            
        except ValueError as e:
            await message.reply(f"❌ Помилка: {str(e)}")
        except Exception as e:
            await message.reply("❌ Сталася помилка при закритті позиції")
    
    async def _handle_positions(self, message: Message) -> None:
        """Handle /positions command"""
        try:
            positions = await self.position_manager.get_positions()
            
            if not positions:
                await message.reply("📊 Немає відкритих позицій")
                return
            
            positions_text = "\n\n".join(
                f"ID: {p.id}\n"
                f"Токен: {p.token}\n"
                f"Кількість: {p.amount}\n"
                f"Ціна входу: {p.entry_price}"
                for p in positions
            )
            
            await message.reply(f"📊 Відкриті позиції:\n\n{positions_text}")
            
        except Exception as e:
            await message.reply("❌ Сталася помилка при отриманні позицій")
    
    async def _handle_balance(self, message: Message) -> None:
        """Handle /balance command"""
        try:
            # TODO: Implement balance checking
            await message.reply("💰 Функція перевірки балансу в розробці")
        except Exception as e:
            await message.reply("❌ Сталася помилка при отриманні балансу")
    
    async def start(self) -> None:
        """Start the bot"""
        try:
            await self.dp.start_polling()
        except Exception as e:
            print(f"Error starting bot: {e}")
    
    async def stop(self) -> None:
        """Stop the bot"""
        try:
            await self.dp.stop_polling()
            await self.bot.close()
        except Exception as e:
            print(f"Error stopping bot: {e}")
    
    async def send_message(self, chat_id: int, text: str) -> Optional[Message]:
        """Send message to specified chat"""
        try:
            return await self.bot.send_message(chat_id=chat_id, text=text)
        except Exception as e:
            print(f"Error sending message: {e}")
            return None

class NotificationService(BaseService):
    """Service for sending notifications to users"""
    
    def __init__(self, token: str, notification_chat_ids: List[int]):
        """Initialize notification service"""
        self.bot = Bot(token=token)
        self.notification_chat_ids = notification_chat_ids
    
    async def start(self) -> None:
        """Start the service"""
        # Nothing to start for notification service
        pass
    
    async def stop(self) -> None:
        """Stop the service"""
        await self.bot.close()
    
    async def send_message(self, chat_id: int, text: str) -> Optional[Message]:
        """Send message to specified chat"""
        try:
            return await self.bot.send_message(chat_id=chat_id, text=text)
        except Exception as e:
            print(f"Error sending message: {e}")
            return None
    
    async def broadcast(self, text: str) -> List[Optional[Message]]:
        """Send message to all notification chats"""
        messages = []
        for chat_id in self.notification_chat_ids:
            message = await self.send_message(chat_id, text)
            messages.append(message)
        return messages
    
    async def notify_position_opened(self, position_id: int, token: str, amount: float, price: float) -> None:
        """Send notification about opened position"""
        text = (
            "📈 Відкрито нову позицію:\n"
            f"ID: {position_id}\n"
            f"Токен: {token}\n"
            f"Кількість: {amount}\n"
            f"Ціна: {price}"
        )
        await self.broadcast(text)
    
    async def notify_position_closed(self, position_id: int, profit: float) -> None:
        """Send notification about closed position"""
        text = (
            "📉 Закрито позицію:\n"
            f"ID: {position_id}\n"
            f"Прибуток: {profit}"
        )
        await self.broadcast(text)
    
    async def notify_error(self, error_message: str) -> None:
        """Send notification about error"""
        text = f"❌ Помилка: {error_message}"
        await self.broadcast(text)
    
    async def notify_balance_update(self, new_balance: float) -> None:
        """Send notification about balance update"""
        text = f"💰 Оновлення балансу: {new_balance}"
        await self.broadcast(text)

class MonitoringService(BaseService):
    """Service for system monitoring"""
    
    def __init__(self, token: str, monitoring_chat_ids: List[int], check_interval: int = 300):
        """Initialize monitoring service"""
        self.bot = Bot(token=token)
        self.monitoring_chat_ids = monitoring_chat_ids
        self.check_interval = check_interval
        self._monitoring_task = None
    
    async def start(self) -> None:
        """Start monitoring service"""
        if not self._monitoring_task:
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
    
    async def stop(self) -> None:
        """Stop monitoring service"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            self._monitoring_task = None
        await self.bot.close()
    
    async def send_message(self, chat_id: int, text: str) -> Optional[Message]:
        """Send message to specified chat"""
        try:
            return await self.bot.send_message(chat_id=chat_id, text=text)
        except Exception as e:
            print(f"Error sending message: {e}")
            return None
    
    async def broadcast(self, text: str) -> List[Optional[Message]]:
        """Send message to all monitoring chats"""
        messages = []
        for chat_id in self.monitoring_chat_ids:
            message = await self.send_message(chat_id, text)
            messages.append(message)
        return messages
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        while True:
            try:
                # Get system stats
                stats = self._get_system_stats()
                
                # Format message
                message = self._format_monitoring_message(stats)
                
                # Send to all chats
                await self.broadcast(message)
                
                # Wait for next check
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                error_message = f"❌ Помилка моніторингу: {str(e)}"
                await self.broadcast(error_message)
                await asyncio.sleep(self.check_interval)
    
    def _get_system_stats(self) -> Dict[str, Any]:
        """Get current system statistics"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'timestamp': datetime.now(),
            'system': {
                'platform': platform.system(),
                'version': platform.version(),
                'machine': platform.machine()
            },
            'cpu': {
                'percent': cpu_percent,
                'cores': psutil.cpu_count()
            },
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent
            },
            'disk': {
                'total': disk.total,
                'free': disk.free,
                'percent': disk.percent
            }
        }
    
    def _format_monitoring_message(self, stats: Dict[str, Any]) -> str:
        """Format monitoring stats as message"""
        return (
            "📊 Системний моніторинг\n\n"
            f"🕒 Час: {stats['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            "💻 Система:\n"
            f"- Платформа: {stats['system']['platform']}\n"
            f"- Версія: {stats['system']['version']}\n"
            f"- Архітектура: {stats['system']['machine']}\n\n"
            "🔄 CPU:\n"
            f"- Завантаження: {stats['cpu']['percent']}%\n"
            f"- Ядра: {stats['cpu']['cores']}\n\n"
            "📝 Пам'ять:\n"
            f"- Всього: {self._format_bytes(stats['memory']['total'])}\n"
            f"- Доступно: {self._format_bytes(stats['memory']['available'])}\n"
            f"- Використано: {stats['memory']['percent']}%\n\n"
            "💾 Диск:\n"
            f"- Всього: {self._format_bytes(stats['disk']['total'])}\n"
            f"- Вільно: {self._format_bytes(stats['disk']['free'])}\n"
            f"- Використано: {stats['disk']['percent']}%"
        )
    
    def _format_bytes(self, bytes: int) -> str:
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024
        return f"{bytes:.2f} PB"

class TelegramHandler(logging.Handler):
    """Custom logging handler that sends logs to Telegram"""
    
    def __init__(self, service: 'LoggingService'):
        """Initialize handler with logging service"""
        super().__init__()
        self.service = service
        
        # Set formatter
        formatter = logging.Formatter(
            "📝 %(levelname)s [%(asctime)s]\n"
            "📂 %(name)s\n"
            "📍 %(funcName)s:%(lineno)d\n"
            "📄 %(message)s"
        )
        self.setFormatter(formatter)
    
    def emit(self, record: logging.LogRecord) -> None:
        """Send log record to Telegram"""
        try:
            msg = self.format(record)
            asyncio.create_task(self.service.broadcast(msg))
        except Exception as e:
            print(f"Error sending log to Telegram: {e}")

class LoggingService(BaseService):
    """Service for sending logs to Telegram"""
    
    def __init__(self, token: str, logging_chat_ids: List[int], min_level: int = logging.INFO):
        """Initialize logging service"""
        self.bot = Bot(token=token)
        self.logging_chat_ids = logging_chat_ids
        
        # Create handler
        self.handler = TelegramHandler(self)
        self.handler.setLevel(min_level)
        
        # Get root logger
        self.logger = logging.getLogger()
        self.logger.addHandler(self.handler)
    
    async def start(self) -> None:
        """Start logging service"""
        startup_message = (
            "🚀 Логування запущено\n"
            f"🕒 Час: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"📊 Мінімальний рівень: {logging.getLevelName(self.handler.level)}"
        )
        await self.broadcast(startup_message)
    
    async def stop(self) -> None:
        """Stop logging service"""
        # Remove handler from root logger
        self.logger.removeHandler(self.handler)
        
        # Send shutdown message
        shutdown_message = (
            "🛑 Логування зупинено\n"
            f"🕒 Час: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        await self.broadcast(shutdown_message)
        
        # Close bot
        await self.bot.close()
    
    async def send_message(self, chat_id: int, text: str) -> Optional[Message]:
        """Send message to specified chat"""
        try:
            return await self.bot.send_message(chat_id=chat_id, text=text)
        except Exception as e:
            print(f"Error sending message: {e}")
            return None
    
    async def broadcast(self, text: str) -> List[Optional[Message]]:
        """Send message to all logging chats"""
        messages = []
        for chat_id in self.logging_chat_ids:
            message = await self.send_message(chat_id, text)
            messages.append(message)
        return messages

class TelegramService:
    """Main service for managing all Telegram bots"""
    
    def __init__(self):
        """Initialize Telegram service"""
        if not self._validate_config():
            raise ValueError("Invalid Telegram configuration")
            
        self.management_bot = ManagementBot(
            token=MANAGEMENT_BOT_TOKEN,
            admin_ids=ADMIN_CHAT_IDS
        )
        
        self.notification_service = NotificationService(
            token=NOTIFICATION_BOT_TOKEN,
            notification_chat_ids=NOTIFICATION_CHAT_IDS
        )
        
        self.monitoring_service = MonitoringService(
            token=MONITORING_BOT_TOKEN,
            monitoring_chat_ids=MONITORING_CHAT_IDS,
            check_interval=MONITORING_CHECK_INTERVAL
        )
        
        self.logging_service = LoggingService(
            token=LOGGING_BOT_TOKEN,
            logging_chat_ids=LOGGING_CHAT_IDS,
            min_level=LOGGING_MIN_LEVEL
        )
    
    def _validate_config(self) -> bool:
        """Validate Telegram configuration"""
        if not MANAGEMENT_BOT_TOKEN:
            print("❌ TELEGRAM_MANAGEMENT_BOT_TOKEN not set")
            return False
            
        if not NOTIFICATION_BOT_TOKEN:
            print("❌ TELEGRAM_NOTIFICATION_BOT_TOKEN not set")
            return False
            
        if not MONITORING_BOT_TOKEN:
            print("❌ TELEGRAM_MONITORING_BOT_TOKEN not set")
            return False
            
        if not LOGGING_BOT_TOKEN:
            print("❌ TELEGRAM_LOGGING_BOT_TOKEN not set")
            return False
            
        if not ADMIN_CHAT_IDS:
            print("❌ TELEGRAM_ADMIN_CHAT_IDS not set")
            return False
            
        if not NOTIFICATION_CHAT_IDS:
            print("❌ TELEGRAM_NOTIFICATION_CHAT_IDS not set")
            return False
            
        if not MONITORING_CHAT_IDS:
            print("❌ TELEGRAM_MONITORING_CHAT_IDS not set")
            return False
            
        if not LOGGING_CHAT_IDS:
            print("❌ TELEGRAM_LOGGING_CHAT_IDS not set")
            return False
            
        return True
    
    async def start(self) -> None:
        """Start all Telegram services"""
        try:
            # Start management bot
            await self.management_bot.start()
            print("✅ Management bot started")
            
            # Start notification service
            await self.notification_service.start()
            print("✅ Notification service started")
            
            # Start monitoring service
            await self.monitoring_service.start()
            print("✅ Monitoring service started")
            
            # Start logging service
            await self.logging_service.start()
            print("✅ Logging service started")
            
        except Exception as e:
            print(f"❌ Error starting Telegram services: {e}")
            await self.stop()
    
    async def stop(self) -> None:
        """Stop all Telegram services"""
        try:
            # Stop management bot
            await self.management_bot.stop()
            print("✅ Management bot stopped")
            
            # Stop notification service
            await self.notification_service.stop()
            print("✅ Notification service stopped")
            
            # Stop monitoring service
            await self.monitoring_service.stop()
            print("✅ Monitoring service stopped")
            
            # Stop logging service
            await self.logging_service.stop()
            print("✅ Logging service stopped")
            
        except Exception as e:
            print(f"❌ Error stopping Telegram services: {e}")
    
    @classmethod
    async def create_and_start(cls) -> Optional['TelegramService']:
        """Create and start Telegram service"""
        try:
            service = cls()
            await service.start()
            return service
        except Exception as e:
            print(f"❌ Error creating Telegram service: {e}")
            return None 