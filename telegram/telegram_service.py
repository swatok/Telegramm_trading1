import asyncio
from typing import Optional

from telegram.config import (
    MANAGEMENT_BOT_TOKEN,
    NOTIFICATION_BOT_TOKEN,
    MONITORING_BOT_TOKEN,
    LOGGING_BOT_TOKEN,
    ADMIN_CHAT_IDS,
    NOTIFICATION_CHAT_IDS,
    MONITORING_CHAT_IDS,
    LOGGING_CHAT_IDS,
    MONITORING_CHECK_INTERVAL,
    LOGGING_MIN_LEVEL,
    validate_config
)
from telegram.management_bot.management_bot import ManagementBot
from telegram.notification_service.notification_service import NotificationService
from telegram.monitoring_service.monitoring_service import MonitoringService
from telegram.logging_service.logging_service import LoggingService

class TelegramService:
    """Main service for managing all Telegram bots"""
    
    def __init__(self):
        """Initialize Telegram service"""
        if not validate_config():
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