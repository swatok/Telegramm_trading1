"""
Парсер системних повідомлень
"""

from datetime import datetime
from typing import Optional
from loguru import logger

from .base_message_parser import BaseMessageParser

class SystemMessageParser(BaseMessageParser):
    def __init__(self):
        super().__init__()
        self.system_keywords = [
            'system', 'maintenance', 'update', 'upgrade',
            'downtime', 'restart', 'backup', 'restore'
        ]
    
    def parse(self, text: str) -> Optional[dict]:
        """Парсинг системного повідомлення"""
        try:
            if not text:
                logger.debug("Порожнє повідомлення")
                return None
                
            text = self._clean_text(text)
            
            # Перевіряємо чи це системне повідомлення
            if not any(keyword in text for keyword in self.system_keywords):
                logger.debug("Не знайдено системних ключових слів")
                return None
            
            # Створюємо системне повідомлення
            message = {
                'type': 'system',
                'timestamp': datetime.now(),
                'raw_text': text,
                'priority': self._determine_priority(text)
            }
            
            logger.info(f"Розпізнано системне повідомлення: {message}")
            return message
            
        except Exception as e:
            logger.error(f"Помилка парсингу системного повідомлення: {e}")
            return None
            
    def _determine_priority(self, text: str) -> str:
        """Визначення пріоритету повідомлення"""
        if any(word in text for word in ['urgent', 'critical', 'emergency']):
            return 'high'
        elif any(word in text for word in ['warning', 'attention']):
            return 'medium'
        return 'low' 