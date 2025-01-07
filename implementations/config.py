from typing import Dict, Any, Optional
import os
import json
from dotenv import load_dotenv
from interfaces.config_interface import ConfigInterface

class ConfigImplementation(ConfigInterface):
    """Імплементація для управління конфігурацією"""
    
    def __init__(self):
        """Ініціалізація конфігурації"""
        self.config = {}
        self.env_file = '.env'
        self.config_file = 'config.json'
        
    async def load(self) -> bool:
        """Завантаження конфігурації"""
        try:
            # Завантажуємо змінні середовища
            load_dotenv(self.env_file)
            
            # Завантажуємо базові налаштування
            self.config = {
                # API ключі
                'jupiter_api_key': os.getenv('JUPITER_API_KEY'),
                'quicknode_api_key': os.getenv('QUICKNODE_API_KEY'),
                
                # Налаштування мережі
                'network': os.getenv('SOLANA_NETWORK', 'mainnet-beta'),
                'rpc_url': os.getenv('SOLANA_RPC_URL'),
                
                # Налаштування гаманця
                'wallet_path': os.getenv('WALLET_PATH'),
                'wallet_password': os.getenv('WALLET_PASSWORD'),
                
                # Налаштування Telegram
                'telegram_token': os.getenv('TELEGRAM_BOT_TOKEN'),
                'telegram_chat_id': os.getenv('TELEGRAM_CHAT_ID'),
                'telegram_monitor_token': os.getenv('TELEGRAM_MONITOR_TOKEN'),
                'telegram_monitor_chat_id': os.getenv('TELEGRAM_MONITOR_CHAT_ID'),
                
                # Налаштування бази даних
                'db_host': os.getenv('DB_HOST', 'localhost'),
                'db_port': int(os.getenv('DB_PORT', 5432)),
                'db_name': os.getenv('DB_NAME'),
                'db_user': os.getenv('DB_USER'),
                'db_password': os.getenv('DB_PASSWORD'),
                
                # Налаштування логування
                'log_level': os.getenv('LOG_LEVEL', 'INFO'),
                'log_file': os.getenv('LOG_FILE', 'bot.log'),
                
                # Налаштування торгівлі
                'min_order_size': float(os.getenv('MIN_ORDER_SIZE', 0.1)),
                'max_order_size': float(os.getenv('MAX_ORDER_SIZE', 10.0)),
                'default_slippage': float(os.getenv('DEFAULT_SLIPPAGE', 1.0)),
                
                # Налаштування моніторингу
                'monitoring_interval': int(os.getenv('MONITORING_INTERVAL', 60)),
                'alert_threshold': float(os.getenv('ALERT_THRESHOLD', 5.0))
            }
            
            # Завантажуємо додаткові налаштування з JSON файлу
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    additional_config = json.load(f)
                    self.config.update(additional_config)
            
            return True
            
        except Exception as e:
            print(f"Error loading config: {e}")
            return False
            
    async def get(self, key: str) -> Optional[Any]:
        """Отримання значення за ключем"""
        return self.config.get(key)
        
    async def set(self, key: str, value: Any) -> bool:
        """Встановлення значення за ключем"""
        try:
            self.config[key] = value
            return True
        except Exception as e:
            print(f"Error setting config value: {e}")
            return False
            
    async def save(self) -> bool:
        """Збереження конфігурації"""
        try:
            # Зберігаємо додаткові налаштування в JSON файл
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
            
    async def reload(self) -> bool:
        """Перезавантаження конфігурації"""
        return await self.load()
        
    async def get_all(self) -> Dict[str, Any]:
        """Отримання всієї конфігурації"""
        return self.config.copy() 