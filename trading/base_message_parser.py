"""
Базовий клас для парсингу повідомлень
"""

import re
from typing import Optional, Dict, Pattern
from loguru import logger

class BaseMessageParser:
    def __init__(self):
        """Ініціалізація базового парсера"""
        self.patterns: Dict[str, Pattern] = {
            'token_address': re.compile(r'[1-9A-HJ-NP-Za-km-z]{32,44}|(?:0x)?[a-fA-F0-9]{40}'),
            'amount': re.compile(r'\d+(?:\.\d+)?'),
            'price': re.compile(r'\d+(?:\.\d+)?'),
            'percent': re.compile(r'\d+(?:\.\d+)?%')
        }
    
    def _find_pattern(self, pattern: Pattern, text: str) -> Optional[str]:
        """Пошук патерну в тексті"""
        match = pattern.search(text)
        return match.group() if match else None
    
    def _clean_text(self, text: str) -> str:
        """Очищення тексту від зайвих символів"""
        return text.strip().lower()
    
    def parse(self, text: str) -> Optional[dict]:
        """
        Базовий метод парсингу, який має бути перевизначений в нащадках
        """
        raise NotImplementedError("Метод parse() має бути реалізований в класі-нащадку") 