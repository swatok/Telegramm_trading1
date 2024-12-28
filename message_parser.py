"""
Модуль для парсингу повідомлень та створення торгових сигналів
"""

import re
import os
from datetime import datetime
from decimal import Decimal
from typing import Optional
from loguru import logger

from model.signal import Signal
from model.token import Token

class MessageParser:
    def __init__(self):
        """Ініціалізація парсера повідомлень"""
        self.patterns = {
            'token_address': r'[1-9A-HJ-NP-Za-km-z]{32,44}|(?:0x)?[a-fA-F0-9]{40}',
            'amount': r'\d+(?:\.\d+)?',
            'price': r'\d+(?:\.\d+)?',
            'percent': r'\d+(?:\.\d+)?%'
        }
        
    def parse(self, text: str) -> Optional[dict]:
        """Парсинг повідомлення для пошуку торгових сигналів"""
        try:
            # Якщо повідомлення порожнє
            if not text:
                logger.debug("Порожнє повідомлення")
                return None
                
            # Шукаємо адресу токена
            token_match = re.search(self.patterns['token_address'], text.strip())
            if not token_match:
                logger.debug("Адреса токена не знайдена")
                return None
                
            token_address = token_match.group().strip()
            logger.debug(f"Знайдено адресу токена: {token_address}")
            
            # Визначаємо тип сигналу
            signal_type = 'buy'  # За замовчуванням buy
            if any(word in text.lower() for word in ['sell', 'short', 'продати']):
                signal_type = 'sell'
            logger.debug(f"Визначено тип сигналу: {signal_type}")
            
            # Створюємо сигнал
            signal = {
                'token_address': token_address,
                'token_name': 'Unknown',  # Буде оновлено пізніше
                'signal_type': signal_type,
                'timestamp': datetime.now(),
                'raw_text': text
            }
            
            # Шукаємо ціну
            price = None
            # Спочатку шукаємо ціну з міткою
            price_patterns = [
                r'(?:price|ціна|price:|ціна:)\s*(\d+(?:\.\d+)?)',
                r'(?:за|at)\s*(\d+(?:\.\d+)?)',
                r'(\d+(?:\.\d+)?)\s*(?:sol|сол|solana)'
            ]
            
            for pattern in price_patterns:
                price_match = re.search(pattern, text.lower())
                if price_match:
                    price = float(price_match.group(1))
                    break
                    
            # Якщо не знайдено ціну з міткою, шукаємо просто число
            if price is None:
                price_match = re.search(self.patterns['price'], text)
                if price_match:
                    price = float(price_match.group())
                    
            signal['price'] = price if price is not None else 2.0  # За замовчуванням 2 SOL
            logger.debug(f"Встановлено ціну: {signal['price']}")
            
            # Шукаємо кількість
            amount = None
            # Спочатку шукаємо кількість з міткою
            amount_patterns = [
                r'(?:amount|кількість|amount:|кількість:)\s*(\d+(?:\.\d+)?)',
                r'(?:buy|купити)\s*(\d+(?:\.\d+)?)',
                r'(\d+(?:\.\d+)?)\s*(?:tokens|токенів)'
            ]
            
            for pattern in amount_patterns:
                amount_match = re.search(pattern, text.lower())
                if amount_match:
                    amount = float(amount_match.group(1))
                    break
                    
            # Якщо не знай��ено кількість з міткою, шукаємо просто число
            if amount is None:
                amount_match = re.search(self.patterns['amount'], text)
                if amount_match:
                    amount = float(amount_match.group())
                    
            signal['amount'] = amount if amount is not None else 2.0  # За замовчуванням 2 токени
            logger.debug(f"Встановлено кількість: {signal['amount']}")
            
            logger.info(f"Розпізнано сигнал: {signal}")
            return signal
            
        except Exception as e:
            logger.error(f"Помилка парсингу повідомлення: {e}")
            return None