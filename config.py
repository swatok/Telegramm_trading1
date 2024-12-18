import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging():
    # Створюємо директорію для логів якщо її немає
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Налаштовуємо основний логер
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # Форматування логів
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        '%Y-%m-%d %H:%M:%S'
    )
    
    # Логування в файл
    file_handler = RotatingFileHandler(
        'logs/bot.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Логування в консоль
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Додаємо обробники до логера
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Вс��ановлюємо рівень логування для сторонніх бібліотек
    logging.getLogger('telethon').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    return logger 