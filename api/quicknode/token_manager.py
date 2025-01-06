"""
Модуль для низькорівневих операцій з токенами через QuickNode API.
"""

from typing import Dict, Optional, List
from decimal import Decimal
from loguru import logger

from .base import QuickNodeBase
from .constants import TOKEN_PROGRAM_ID

class TokenManager(QuickNodeBase):
    """
    Клас для низькорівневих операцій з токенами через QuickNode API.
    """

    def __init__(self, http_url: str):
        """
        Ініціалізація менеджера токенів.

        Args:
            http_url: URL для HTTP запитів до QuickNode
        """
        super().__init__(http_url)
        self.token_info_cache: Dict[str, Dict] = {}

    async def verify_token(self, token_address: str) -> Optional[Dict]:
        """
        Перевірка існування токена.

        Args:
            token_address: Адреса токену

        Returns:
            Словник з інформацією про токен або None
        """
        try:
            logger.info(f"Перевірка токена {token_address}")
            
            # Спочатку перевіряємо кеш
            if token_address in self.token_info_cache:
                return self.token_info_cache[token_address]

            # Формуємо запит до Solana RPC
            result = await self._make_request(
                "getAccountInfo",
                [token_address, {"encoding": "jsonParsed", "commitment": "confirmed"}]
            )

            if not result:
                return None

            # Парсимо дані токена
            token_info = {
                'address': token_address,
                'exists': True,
                'source': 'solana'
            }

            # Додаємо інформацію про метадані, якщо вони є
            if 'data' in result and 'parsed' in result['data']:
                parsed_data = result['data']['parsed']
                token_info.update(parsed_data)

            # Зберігаємо в кеш
            self.token_info_cache[token_address] = token_info
            return token_info

        except Exception as e:
            logger.error(f"Помилка перевірки токена {token_address}: {e}")
            return None

    async def get_token_accounts(self, owner_address: str) -> List[Dict]:
        """
        Отримання всіх токенів на гаманці.

        Args:
            owner_address: Адреса гаманця

        Returns:
            Список словників з інформацією про токени
        """
        try:
            result = await self._make_request(
                "getTokenAccountsByOwner",
                [
                    owner_address,
                    {"programId": TOKEN_PROGRAM_ID},
                    {"encoding": "jsonParsed"}
                ]
            )

            if not result or 'value' not in result:
                return []

            accounts = []
            for item in result['value']:
                if 'account' in item and 'data' in item['account']:
                    parsed_data = item['account']['data']['parsed']
                    if 'info' in parsed_data:
                        accounts.append(parsed_data['info'])

            return accounts

        except Exception as e:
            logger.error(f"Помилка отримання токенів для {owner_address}: {e}")
            return []

    async def get_token_balance(self, token_account: str) -> Optional[Decimal]:
        """
        Отримання балансу токена.

        Args:
            token_account: Адреса токен-акаунта

        Returns:
            Баланс токена або None
        """
        try:
            result = await self._make_request(
                "getTokenAccountBalance",
                [token_account]
            )

            if not result or 'value' not in result:
                return None

            amount = result['value'].get('amount')
            decimals = result['value'].get('decimals', 0)

            if amount is None:
                return None

            return Decimal(amount) / Decimal(10 ** decimals)

        except Exception as e:
            logger.error(f"Помилка отримання балансу токена {token_account}: {e}")
            return None

    def clear_cache(self, token_address: Optional[str] = None):
        """
        Очищення кешу інформації про токени.

        Args:
            token_address: Адреса токену для очищення або None для повного очищення
        """
        if token_address:
            self.token_info_cache.pop(token_address, None)
            logger.info(f"Кеш очищено для токену {token_address}")
        else:
            self.token_info_cache.clear()
            logger.info("Кеш токенів повністю очищено") 