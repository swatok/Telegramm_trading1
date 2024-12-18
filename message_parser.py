"""
Модуль для парсингу повідомлень та створення торгових сигналів
"""

import re
from datetime import datetime
from decimal import Decimal
from typing import Optional
from loguru import logger

from model.signal import Signal
from model.token import Token

class MessageParser:
    def __init__(self):
        # Шаблони для парсингу
        self.address_pattern = r'([A-HJ-NP-Za-km-z1-9]{32,44})'  # Шаблон для Solana адрес
        self.price_pattern = r'(\d+\.?\d*)\s*(SOL|USDC|USD)'
        
    def parse_message(self, message: str, message_id: int = None, channel_id: int = None) -> Optional[Signal]:
        """Парсинг повідомлення для виявлення Solana контрактів"""
        try:
            logger.debug(f"Починаємо парсинг повідомлення: {message}")
            
            # Пошук адреси токена
            address_match = re.search(self.address_pattern, message)
            if not address_match:
                logger.warning("Адреса то��ена не знайдена в повідомленні")
                return None
                
            token_address = address_match.group(1)
            logger.debug(f"Знайдено адресу токена: {token_address}")
            
            # Пошук ціни (якщо є)
            price_match = re.search(self.price_pattern, message)
            entry_price = Decimal(price_match.group(1)) if price_match else None
            
            # Створюємо об'єкт Token
            token = Token(
                address=token_address,
                name=f"Token_{token_address[:8]}",
                symbol=f"T{token_address[:4]}",
                decimals=9,  # За замовчуванням для Solana токенів
                verified=False
            )
            
            # Створюємо сигнал
            signal = Signal(
                token_address=token_address,
                action='buy',  # Завжди buy при знаходженні нового контракту
                timestamp=datetime.now(),
                source_type='telegram',
                source_id=str(channel_id) if channel_id else '',
                message_id=message_id,
                entry_price=entry_price,
                amount_sol=Decimal("0.01"),  # Базова кількість для покупки в SOL
                token=token,
                confidence_score=Decimal("1.0"),
                status='new'
            )
            
            logger.info(f"Знайдено новий Solana контракт: {signal}")
            return signal
            
        except Exception as e:
            logger.error(f"Помилка парсингу повідомлення: {e}", exc_info=True)
            return None