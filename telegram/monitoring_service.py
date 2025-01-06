from typing import Optional, List, Dict, Any
from datetime import datetime
import psutil
import platform
import asyncio
import re

from aiogram import Bot
from aiogram.types import Message
from telethon import TelegramClient, events

from interfaces.telegram_interfaces import BaseService

class MonitoringService(BaseService):
    """Service for system monitoring and channel monitoring"""
    
    def __init__(self, 
                 token: str, 
                 monitoring_chat_ids: List[int],
                 api_id: str,
                 api_hash: str,
                 session_name: str,
                 target_channels: List[int],
                 check_interval: int = 300):
        """Initialize monitoring service"""
        # Bot initialization
        self.bot = Bot(token=token)
        self.monitoring_chat_ids = monitoring_chat_ids
        self.check_interval = check_interval
        self._monitoring_task = None
        
        # Channel monitoring initialization
        self.client = TelegramClient(session_name, api_id, api_hash)
        self.target_channels = target_channels
        self._channel_monitoring_task = None
        self.contract_pattern = r"([1-9A-HJ-NP-Za-km-z]{32,44})"

    async def start(self) -> None:
        """Start monitoring service"""
        # Start system monitoring
        if not self._monitoring_task:
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        # Start channel monitoring
        if not self._channel_monitoring_task:
            await self.client.start()
            self._setup_channel_monitoring()
            self._channel_monitoring_task = asyncio.create_task(self.client.run_until_disconnected())

    async def stop(self) -> None:
        """Stop monitoring service"""
        # Stop system monitoring
        if self._monitoring_task:
            self._monitoring_task.cancel()
            self._monitoring_task = None
        
        # Stop channel monitoring
        if self._channel_monitoring_task:
            self._channel_monitoring_task.cancel()
            await self.client.disconnect()
            self._channel_monitoring_task = None
        
        await self.bot.close()

    def _setup_channel_monitoring(self) -> None:
        """Setup channel monitoring handlers"""
        @self.client.on(events.NewMessage(chats=self.target_channels))
        async def handle_new_message(event):
            message = event.message.text
            contract_data = await self._parse_message(message)
            
            if contract_data:
                await self.broadcast(
                    f"🔍 Знайдено новий контракт:\n"
                    f"Адреса: {contract_data['contract_address']}\n"
                    f"Час: {contract_data['timestamp']}"
                )

    async def _parse_message(self, message: str) -> Optional[Dict[str, Any]]:
        """Parse message for contract address"""
        try:
            contract_match = re.search(self.contract_pattern, message)
            if not contract_match:
                return None

            return {
                "contract_address": contract_match.group(1),
                "raw_message": message,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            await self.broadcast(f"❌ Помилка парсингу повідомлення: {str(e)}")
            return None

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