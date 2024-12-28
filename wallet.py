"""Wallet module"""

import os
import base58
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.message import Message
import base64
from loguru import logger
from typing import Optional, Dict
import aiohttp

class Wallet:
    def __init__(self):
        """Ініціалізація гаманця"""
        try:
            # Отримуємо ключі з .env
            private_key = os.getenv('SOLANA_PRIVATE_KEY')
            expected_public_key = os.getenv('SOLANA_PUBLIC_KEY')
            
            if not private_key:
                raise ValueError("SOLANA_PRIVATE_KEY не знайдено в змінних середовища")
            if not expected_public_key:
                raise ValueError("SOLANA_PUBLIC_KEY не знайдено в змінних середовища")
                
            # Створюємо keypair
            private_key_bytes = base58.b58decode(private_key)
            self.keypair = Keypair.from_bytes(private_key_bytes)
            
            # Перевіряємо відповідність публічного ключа
            actual_public_key = str(self.keypair.pubkey())
            if actual_public_key != expected_public_key:
                raise ValueError(f"Публічний ключ з приватного ключа ({actual_public_key}) не відповідає очікуваному ({expected_public_key})")
            
            # Зберігаємо публічний ключ
            self.public_key = actual_public_key
            
            # Ініціалізуємо HTTP сесію
            self.session = None
            
            logger.info("Гаманець успішно ініціалізовано")
            
        except Exception as e:
            logger.error(f"Помилка ініціалізації гаманця: {e}")
            raise
            
    def sign_transaction(self, transaction: Transaction) -> bytes:
        """Підписання транзакції"""
        try:
            # Підписуємо транзакцію
            transaction.sign([self.keypair])
            return transaction.serialize()
        except Exception as e:
            logger.error(f"Помилка підписання транзакції: {e}")
            raise
            
    def sign_message(self, message: bytes) -> bytes:
        """Підписання повідомлення"""
        try:
            # Підписуємо повідомлення
            return self.keypair.sign_message(message)
        except Exception as e:
            logger.error(f"Помилка підписання повідомлення: {e}")
            raise
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Отримання HTTP сесії"""
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
        
    async def get_sol_balance(self) -> float:
        """Отримання балансу SOL"""
        try:
            session = await self._get_session()
            url = os.getenv('QUICKNODE_HTTP_URL')
            
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBalance",
                "params": [self.public_key]
            }
            
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'result' in data:
                        # Конвертуємо лампорт в SOL
                        return float(data['result']['value']) / 1e9
                    else:
                        logger.error(f"Помилка отримання балансу: {data.get('error')}")
                        return 0
                else:
                    logger.error(f"Помилка отримання балансу ({response.status}): {await response.text()}")
                    return 0
                    
        except Exception as e:
            logger.error(f"Помилка отримання балансу: {e}")
            return 0
            
    async def close(self):
        """Закриття сесії"""
        if self.session and not self.session.closed:
            await self.session.close() 