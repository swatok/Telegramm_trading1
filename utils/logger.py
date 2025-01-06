import logging
import os
from datetime import datetime

class Logger:
    def __init__(self, name: str, log_dir: str = "logs"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Створюємо директорію для логів якщо вона не існує
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # Формат логування
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Файловий обробник
        log_file = os.path.join(
            log_dir, 
            f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # Консольний обробник
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # Додаємо обробники до логера
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def debug(self, message: str):
        self.logger.debug(message)
        
    def info(self, message: str):
        self.logger.info(message)
        
    def warning(self, message: str):
        self.logger.warning(message)
        
    def error(self, message: str):
        self.logger.error(message)
        
    def critical(self, message: str):
        self.logger.critical(message)

# Створюємо глобальний логер
def get_logger(name: str) -> Logger:
    return Logger(name)
