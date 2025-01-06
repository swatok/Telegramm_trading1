from typing import List
import os
import logging
from dotenv import load_dotenv

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

# Monitoring settings
MONITORING_CHECK_INTERVAL = int(os.getenv('TELEGRAM_MONITORING_INTERVAL', '300'))  # 5 minutes default

# Logging settings
LOGGING_MIN_LEVEL = getattr(logging, os.getenv('TELEGRAM_LOGGING_MIN_LEVEL', 'INFO'))

# Validate configuration
def validate_config() -> bool:
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