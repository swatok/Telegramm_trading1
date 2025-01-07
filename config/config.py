"""Configuration management"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass

@dataclass
class Config:
    """Централізована конфігурація"""
    
    def __init__(self, config_path: Optional[str] = None):
        self._config: Dict[str, Any] = {}
        self._load_default_config()
        if config_path:
            self._load_custom_config(config_path)
        
    def _load_default_config(self) -> None:
        """Завантаження дефолтної конфігурації"""
        default_path = Path(__file__).parent / "default_config.yaml"
        if default_path.exists():
            with open(default_path) as f:
                self._config = yaml.safe_load(f)
    
    def _load_custom_config(self, config_path: str) -> None:
        """Завантаження користувацької конфігурації"""
        custom_path = Path(config_path)
        if custom_path.exists():
            with open(custom_path) as f:
                custom_config = yaml.safe_load(f)
                # Рекурсивне оновлення конфігурації
                self._update_dict(self._config, custom_config)
    
    def _update_dict(self, d1: dict, d2: dict) -> None:
        """Рекурсивне оновлення словника"""
        for k, v in d2.items():
            if k in d1 and isinstance(d1[k], dict) and isinstance(v, dict):
                self._update_dict(d1[k], v)
            else:
                d1[k] = v
    
    def get(self, key: str, default: Any = None) -> Any:
        """Отримання значення з пріоритетом: ENV > custom config > default config"""
        # Спочатку перевіряємо змінні оточення
        env_key = f"TRADING_{key.upper()}"
        env_value = os.getenv(env_key)
        if env_value is not None:
            return env_value
            
        # Потім шукаємо в конфігурації
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default
    
    @property
    def database(self) -> Dict[str, Any]:
        """Налаштування бази даних"""
        return {
            'host': self.get('database.host', 'localhost'),
            'port': int(self.get('database.port', 5432)),
            'database': self.get('database.name', 'trading_db'),
            'user': self.get('database.user', 'postgres'),
            'password': self.get('database.password', ''),
            'min_size': int(self.get('database.pool.min_size', 10)),
            'max_size': int(self.get('database.pool.max_size', 20)),
            'ssl_mode': self.get('database.ssl_mode')
        }
    
    @property
    def logging(self) -> Dict[str, Any]:
        """Налаштування логування"""
        return {
            'level': self.get('logging.level', 'INFO'),
            'format': self.get('logging.format'),
            'dir': self.get('logging.dir', 'logs'),
            'file_size': int(self.get('logging.file_size_mb', 10)),
            'backup_count': int(self.get('logging.backup_count', 5))
        }
    
    @property
    def security(self) -> Dict[str, Any]:
        """Налаштування безпеки"""
        return {
            'jwt_algorithm': self.get('security.jwt_algorithm', 'HS256'),
            'jwt_expiration': int(self.get('security.jwt_expiration_minutes', 60)),
            'allowed_ips': self.get('security.allowed_ips', ['127.0.0.1']),
            'rate_limit': int(self.get('security.rate_limit', 100)),
            'max_request_size': int(self.get('security.max_request_size_mb', 10))
        }
    
    @property
    def telegram(self) -> Dict[str, Any]:
        """Налаштування Telegram"""
        return {
            'bot_token': self.get('telegram.bot_token'),
            'admin_ids': self.get('telegram.admin_ids', []),
            'notification_types': self.get('telegram.notification_types', [])
        }
    
    @property
    def trading(self) -> Dict[str, Any]:
        """Налаштування торгівлі"""
        return {
            'max_position_size': float(self.get('trading.position.max_size', 0.1)),
            'min_position_size': float(self.get('trading.position.min_size', 0.01)),
            'max_slippage': float(self.get('trading.slippage.max', 0.01)),
            'default_stop_loss': float(self.get('trading.risk.default_stop_loss', 0.02)),
            'default_take_profit': float(self.get('trading.risk.default_take_profit', 0.04))
        }
    
    @property
    def monitoring(self) -> Dict[str, Any]:
        """Налаштування моніторингу"""
        return {
            'update_interval': int(self.get('monitoring.update_interval', 60)),
            'alert_threshold': float(self.get('monitoring.alert_threshold', 0.05)),
            'metrics_retention_days': int(self.get('monitoring.metrics_retention_days', 30))
        }

# Створюємо глобальний екземпляр конфігурації
config = Config() 