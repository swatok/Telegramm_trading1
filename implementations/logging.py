from typing import Dict, Any, Optional
import logging
import json
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from interfaces.logging_interface import LoggingInterface

class LoggingImplementation(LoggingInterface):
    """Імплементація для системи логування"""
    
    def __init__(self):
        """Ініціалізація системи логування"""
        self.logger = None
        self.config = {}
        self.log_dir = 'logs'
        self.max_file_size = 10 * 1024 * 1024  # 10 MB
        self.backup_count = 5
        
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Ініціалізація логування"""
        try:
            self.config = config
            
            # Створюємо директорію для логів якщо її немає
            if not os.path.exists(self.log_dir):
                os.makedirs(self.log_dir)
                
            # Налаштовуємо основний логер
            self.logger = logging.getLogger('trading_bot')
            self.logger.setLevel(getattr(logging, config.get('log_level', 'INFO')))
            
            # Налаштовуємо форматування
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
            # Додаємо обробник для файлу
            file_handler = RotatingFileHandler(
                os.path.join(self.log_dir, 'bot.log'),
                maxBytes=self.max_file_size,
                backupCount=self.backup_count
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            
            # Додаємо обробник для помилок
            error_handler = RotatingFileHandler(
                os.path.join(self.log_dir, 'error.log'),
                maxBytes=self.max_file_size,
                backupCount=self.backup_count
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)
            self.logger.addHandler(error_handler)
            
            # Додаємо обробник для консолі
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            
            return True
            
        except Exception as e:
            print(f"Error initializing logging: {e}")
            return False
            
    async def log(self, level: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Запис логу"""
        try:
            if not self.logger:
                return False
                
            # Отримуємо рівень логування
            log_level = getattr(logging, level.upper(), logging.INFO)
            
            # Форматуємо повідомлення з метаданими
            formatted_message = message
            if metadata:
                formatted_message = f"{message} | Metadata: {json.dumps(metadata)}"
                
            # Записуємо лог
            self.logger.log(log_level, formatted_message)
            return True
            
        except Exception as e:
            print(f"Error logging message: {e}")
            return False
            
    async def get_logs(self, level: Optional[str] = None, start_time: Optional[datetime] = None,
                      end_time: Optional[datetime] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Отримання логів"""
        try:
            logs = []
            log_file = os.path.join(self.log_dir, 'bot.log')
            
            if not os.path.exists(log_file):
                return logs
                
            # Читаємо логи з файлу
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        # Парсимо рядок логу
                        parts = line.split(' - ')
                        if len(parts) >= 4:
                            timestamp = datetime.strptime(parts[0], '%Y-%m-%d %H:%M:%S,%f')
                            log_level = parts[2].strip()
                            message = ' - '.join(parts[3:]).strip()
                            
                            # Фільтруємо за рівнем
                            if level and log_level.upper() != level.upper():
                                continue
                                
                            # Фільтруємо за часом
                            if start_time and timestamp < start_time:
                                continue
                            if end_time and timestamp > end_time:
                                continue
                                
                            # Додаємо лог
                            logs.append({
                                'timestamp': timestamp.isoformat(),
                                'level': log_level,
                                'message': message
                            })
                            
                            # Перевіряємо ліміт
                            if len(logs) >= limit:
                                break
                                
                    except Exception as e:
                        print(f"Error parsing log line: {e}")
                        continue
                        
            return logs
            
        except Exception as e:
            print(f"Error getting logs: {e}")
            return []
            
    async def clear_logs(self) -> bool:
        """Очищення логів"""
        try:
            # Очищуємо всі файли логів
            for filename in os.listdir(self.log_dir):
                if filename.endswith('.log'):
                    file_path = os.path.join(self.log_dir, filename)
                    with open(file_path, 'w') as f:
                        f.truncate(0)
                        
            return True
            
        except Exception as e:
            print(f"Error clearing logs: {e}")
            return False
            
    async def set_level(self, level: str) -> bool:
        """Встановлення рівня логування"""
        try:
            if not self.logger:
                return False
                
            # Встановлюємо новий рівень
            log_level = getattr(logging, level.upper(), None)
            if log_level:
                self.logger.setLevel(log_level)
                return True
                
            return False
            
        except Exception as e:
            print(f"Error setting log level: {e}")
            return False 