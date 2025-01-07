"""Database configuration"""

from typing import Optional
from dataclasses import dataclass
from os import getenv

@dataclass
class DatabaseConfig:
    """Конфігурація бази даних"""
    host: str
    port: int
    database: str
    user: str
    password: str
    min_size: int = 10
    max_size: int = 20
    ssl_mode: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Створення конфігурації з змінних оточення"""
        return cls(
            host=getenv('DB_HOST', 'localhost'),
            port=int(getenv('DB_PORT', '5432')),
            database=getenv('DB_NAME', 'trading_db'),
            user=getenv('DB_USER', 'postgres'),
            password=getenv('DB_PASSWORD', ''),
            min_size=int(getenv('DB_POOL_MIN_SIZE', '10')),
            max_size=int(getenv('DB_POOL_MAX_SIZE', '20')),
            ssl_mode=getenv('DB_SSL_MODE')
        )
    
    @property
    def dsn(self) -> str:
        """Отримання DSN для підключення"""
        ssl = f"?sslmode={self.ssl_mode}" if self.ssl_mode else ""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}{ssl}"
    
    @property
    def pool_settings(self) -> dict:
        """Налаштування пулу з'єднань"""
        return {
            'min_size': self.min_size,
            'max_size': self.max_size,
            'command_timeout': 60,
            'statement_timeout': 60
        } 