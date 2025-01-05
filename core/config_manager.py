import os
from typing import Any, Dict, Optional
from dotenv import load_dotenv

from utils import get_logger, singleton
from utils.decorators import log_execution
from .env_constants import *

logger = get_logger("config_manager")

@singleton
class ConfigManager:
    def __init__(self):
        """Ініціалізація менеджера конфігурації"""
        self._load_env()
        self._config: Dict[str, Any] = {}
        self._load_default_config()
        self._validate_config()
        self._log_config()
        
    @log_execution
    def _load_env(self):
        """Завантаження змінних оточення"""
        load_dotenv()
        
        # Перевіряємо наявність обов'язкових змінних
        missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Відсутні обов'язкові змінні оточення: {', '.join(missing_vars)}")
            
    @log_execution
    def _load_default_config(self):
        """Завантаження конфігурації за замовчуванням"""
        self._config = {
            'trading': {
                'max_slippage': float(os.getenv('MAX_SLIPPAGE_PERCENT', DEFAULT_MAX_SLIPPAGE)),
                'min_sol_balance': float(os.getenv('MIN_LIQUIDITY_SOL', DEFAULT_MIN_LIQUIDITY)),
                'initial_position_percent': float(os.getenv('INITIAL_POSITION_PERCENT', DEFAULT_POSITION_PERCENT)),
                'max_fdv_usd': float(os.getenv('MAX_FDV_USD', DEFAULT_MAX_FDV)),
                'default_take_profit': float(os.getenv('DEFAULT_TAKE_PROFIT', DEFAULT_TAKE_PROFIT)),
                'default_stop_loss': float(os.getenv('DEFAULT_STOP_LOSS', DEFAULT_STOP_LOSS)),
            },
            
            'monitoring': {
                'price_update_interval': int(os.getenv('PRICE_UPDATE_INTERVAL', DEFAULT_PRICE_UPDATE_INTERVAL)),
                'position_check_interval': int(os.getenv('POSITION_CHECK_INTERVAL', DEFAULT_POSITION_CHECK_INTERVAL)),
                'reconnect_delay': int(os.getenv('RECONNECT_DELAY', DEFAULT_RECONNECT_DELAY)),
                'max_reconnect_attempts': int(os.getenv('MAX_RECONNECT_ATTEMPTS', DEFAULT_MAX_RECONNECT_ATTEMPTS))
            },
            
            'telegram': {
                'session_path': os.getenv('SESSION_PATH', DEFAULT_SESSION_PATH),
                'monitor_session': os.getenv('MONITOR_SESSION', DEFAULT_MONITOR_SESSION),
                'bot_session': os.getenv('BOT_SESSION', DEFAULT_BOT_SESSION),
                'monitor_channel_id': int(os.getenv('MONITOR_CHANNEL_ID')),
                'source_channels': eval(os.getenv('SOURCE_CHANNELS', DEFAULT_SOURCE_CHANNELS)),
                'admin_id': int(os.getenv('ADMIN_ID'))
            },

            'logging': {
                'level': os.getenv('LOG_LEVEL', DEFAULT_LOG_LEVEL),
                'file_path': os.getenv('LOG_FILE_PATH', DEFAULT_LOG_FILE_PATH),
                'format': os.getenv('LOG_FORMAT', DEFAULT_LOG_FORMAT),
                'rotation': os.getenv('LOG_ROTATION', DEFAULT_LOG_ROTATION),
                'compression': os.getenv('LOG_COMPRESSION', DEFAULT_LOG_COMPRESSION)
            }
        }

    def _validate_config(self):
        """Валідація значень конфігурації"""
        trading = self._config['trading']
        
        if not (0 < trading['max_slippage'] <= 100):
            raise ValueError("max_slippage має бути від 0 до 100")
            
        if trading['min_sol_balance'] <= 0:
            raise ValueError("min_sol_balance має бути більше 0")
            
        if not (0 < trading['initial_position_percent'] <= 100):
            raise ValueError("initial_position_percent має бути від 0 до 100")

        if trading['max_fdv_usd'] <= 0:
            raise ValueError("max_fdv_usd має бути більше 0")

        if not (0 < trading['default_take_profit'] <= 1000):
            raise ValueError("default_take_profit має бути від 0 до 1000")

        if not (0 < trading['default_stop_loss'] <= 100):
            raise ValueError("default_stop_loss має бути від 0 до 100")

        monitoring = self._config['monitoring']
        if monitoring['price_update_interval'] <= 0:
            raise ValueError("price_update_interval має бути більше 0")

        if monitoring['position_check_interval'] <= 0:
            raise ValueError("position_check_interval має бути більше 0")

        if monitoring['reconnect_delay'] <= 0:
            raise ValueError("reconnect_delay має бути більше 0")

        if monitoring['max_reconnect_attempts'] <= 0:
            raise ValueError("max_reconnect_attempts має бути більше 0")

    def _log_config(self):
        """Логування поточної конфігурації"""
        logger.info("Поточна конфігурація:")
        for section, values in self._config.items():
            logger.info(f"{section}:")
            for key, value in values.items():
                logger.info(f"  {key}: {value}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Отримання значення конфігурації
        
        Args:
            key: Ключ конфігурації (може бути вкладеним, наприклад 'trading.max_positions')
            default: Значення за замовчуванням
        """
        try:
            value = self._config
            for k in key.split('.'):
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
            
    def set(self, key: str, value: Any):
        """
        Встановлення значення конфігурації
        
        Args:
            key: Ключ конфігурації
            value: Нове значення
        """
        keys = key.split('.')
        target = self._config
        
        for k in keys[:-1]:
            target = target.setdefault(k, {})
            
        target[keys[-1]] = value
        logger.info(f"Оновлено конфігурацію: {key} = {value}")
        
    def get_env(self, key: str, default: Any = None) -> Any:
        """
        Отримання значення зі змінних оточення
        
        Args:
            key: Ключ змінної оточення
            default: Значення за замовчуванням
        """
        return os.getenv(key, default)
        
    @property
    def all_config(self) -> Dict[str, Any]:
        """Отримання всієї конфігурації"""
        return self._config.copy()
        
    def update_config(self, new_config: Dict[str, Any]):
        """
        Оновлення конфігурації
        
        Args:
            new_config: Нова конфігурація
        """
        def update_dict(target: dict, source: dict):
            for key, value in source.items():
                if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                    update_dict(target[key], value)
                else:
                    target[key] = value
                    
        update_dict(self._config, new_config)
        logger.info("Конфігурацію оновлено")
        self._validate_config()
        self._log_config()
