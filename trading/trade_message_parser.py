"""
Парсер торгових повідомлень
"""

import re
from datetime import datetime
from typing import Optional
from loguru import logger

from .base_message_parser import BaseMessageParser

class TradeMessageParser(BaseMessageParser):
    def parse(self, text: str) -> Optional[dict]:
        """Парсинг торгового повідомлення"""
        try:
            if not text:
                logger.debug("Порожнє повідомлення")
                return None
                
            text = self._clean_text(text)
            
            # Шукаємо адресу токена
            token_address = self._find_pattern(self.patterns['token_address'], text)
            if not token_address:
                logger.debug("Адреса токена не знайдена")
                return None
                
            # Визначаємо тип сигналу
            signal_type = 'buy'  # За замовчуванням buy
            if any(word in text for word in ['sell', 'short', 'продати']):
                signal_type = 'sell'
                
            # Створюємо сигнал
            signal = {
                'token_address': token_address,
                'token_name': 'Unknown',
                'signal_type': signal_type,
                'timestamp': datetime.now(),
                'raw_text': text
            }
            
            # Додаємо ціну та кількість
            signal['price'] = self._parse_price(text)
            signal['amount'] = self._parse_amount(text)
            
            logger.info(f"Розпізнано торговий сигнал: {signal}")
            return signal
            
        except Exception as e:
            logger.error(f"Помилка парсингу торгового повідомлення: {e}")
            return None
            
    def _parse_price(self, text: str) -> float:
        """Парсинг ціни з повідомлення"""
        price_patterns = [
            r'(?:price|ціна|price:|ціна:)\s*(\d+(?:\.\d+)?)',
            r'(?:за|at)\s*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*(?:sol|сол|solana)'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text)
            if match:
                return float(match.group(1))
                
        # Якщо не знайдено ціну з міткою, шукаємо просто число
        price = self._find_pattern(self.patterns['price'], text)
        return float(price) if price else 2.0  # За замовчуванням 2 SOL
        
    def _parse_amount(self, text: str) -> float:
        """Парсинг кількості з повідомлення"""
        amount_patterns = [
            r'(?:amount|кількість|amount:|кількість:)\s*(\d+(?:\.\d+)?)',
            r'(?:buy|купити)\s*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*(?:tokens|токенів)'
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, text)
            if match:
                return float(match.group(1))
                
        # Якщо не знайдено кількість з міткою, шукаємо просто число
        amount = self._find_pattern(self.patterns['amount'], text)
        return float(amount) if amount else 2.0  # За замовчуванням 2 токени 