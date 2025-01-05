"""
Парсер повідомлень про помилки
"""

from datetime import datetime
from typing import Optional
from loguru import logger

from .base_message_parser import BaseMessageParser

class ErrorMessageParser(BaseMessageParser):
    def __init__(self):
        super().__init__()
        self.error_keywords = [
            'error', 'exception', 'failed', 'failure',
            'помилка', 'збій', 'невдача', 'rejected'
        ]
    
    def parse(self, text: str) -> Optional[dict]:
        """Парсинг повідомлення про помилку"""
        try:
            if not text:
                logger.debug("Порожнє повідомлення")
                return None
                
            text = self._clean_text(text)
            
            # Перевіряємо чи це повідомлення про помилку
            if not any(keyword in text for keyword in self.error_keywords):
                logger.debug("Не знайдено ключових слів помилки")
                return None
            
            # Створюємо повідомлення про помилку
            message = {
                'type': 'error',
                'timestamp': datetime.now(),
                'raw_text': text,
                'error_type': self._determine_error_type(text),
                'severity': self._determine_severity(text)
            }
            
            logger.info(f"Розпізнано повідомлення про помилку: {message}")
            return message
            
        except Exception as e:
            logger.error(f"Помилка парсингу повідомлення про помилку: {e}")
            return None
            
    def _determine_error_type(self, text: str) -> str:
        """Визначення типу помилки"""
        if 'connection' in text or "з'єднання" in text:
            return 'network'
        elif 'timeout' in text or 'таймаут' in text:
            return 'timeout'
        elif 'permission' in text or 'доступ' in text:
            return 'permission'
        return 'unknown'
        
    def _determine_severity(self, text: str) -> str:
        """Визначення серйозності помилки"""
        if any(word in text for word in ['critical', 'fatal', 'критична']):
            return 'critical'
        elif any(word in text for word in ['warning', 'увага']):
            return 'warning'
        return 'info' 