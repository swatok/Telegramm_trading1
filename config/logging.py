"""Logging configuration"""

import sys
from typing import Dict, Any
from pathlib import Path
from os import getenv
from dataclasses import dataclass

@dataclass
class LoggingConfig:
    """Конфігурація логування"""
    level: str
    format: str
    log_dir: Path
    file_size: int  # в мегабайтах
    backup_count: int
    
    @classmethod
    def from_env(cls) -> 'LoggingConfig':
        """Створення конфігурації з змінних оточення"""
        return cls(
            level=getenv('LOG_LEVEL', 'INFO'),
            format=getenv(
                'LOG_FORMAT',
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ),
            log_dir=Path(getenv('LOG_DIR', 'logs')),
            file_size=int(getenv('LOG_FILE_SIZE_MB', '10')),
            backup_count=int(getenv('LOG_BACKUP_COUNT', '5'))
        )
    
    def get_config(self) -> Dict[str, Any]:
        """Отримання конфігурації для loguru"""
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        return {
            "handlers": [
                {
                    "sink": sys.stderr,
                    "format": self.format,
                    "level": self.level,
                    "colorize": True
                },
                {
                    "sink": str(self.log_dir / "app.log"),
                    "format": self.format,
                    "level": self.level,
                    "rotation": f"{self.file_size} MB",
                    "retention": self.backup_count,
                    "compression": "zip"
                }
            ],
            "extra": {
                "project": "trading_bot"
            }
        }
    
    def get_error_config(self) -> Dict[str, Any]:
        """Отримання конфігурації для логування помилок"""
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        return {
            "handlers": [
                {
                    "sink": str(self.log_dir / "errors.log"),
                    "format": self.format,
                    "level": "ERROR",
                    "rotation": f"{self.file_size} MB",
                    "retention": self.backup_count,
                    "compression": "zip"
                }
            ]
        }
    
    def get_trade_config(self) -> Dict[str, Any]:
        """Отримання конфігурації для логування торгів"""
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        return {
            "handlers": [
                {
                    "sink": str(self.log_dir / "trades.log"),
                    "format": self.format,
                    "level": self.level,
                    "rotation": f"{self.file_size} MB",
                    "retention": self.backup_count,
                    "compression": "zip"
                }
            ]
        }
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Отримання конфігурації для логування метрик продуктивності"""
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        return {
            "handlers": [
                {
                    "sink": str(self.log_dir / "performance.log"),
                    "format": self.format,
                    "level": self.level,
                    "rotation": f"{self.file_size} MB",
                    "retention": self.backup_count,
                    "compression": "zip"
                }
            ]
        } 