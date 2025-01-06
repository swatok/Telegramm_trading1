"""
Модуль для роботи з метаданими токенів через QuickNode API.
"""

import base58
from typing import Dict, Optional
from loguru import logger

from .base import QuickNodeBase

class MetadataManager(QuickNodeBase):
    """
    Клас для роботи з метаданими токенів через QuickNode API.
    """

    def __init__(self, http_url: str):
        """
        Ініціалізація менеджера метаданих.

        Args:
            http_url: URL для HTTP запитів до QuickNode
        """
        super().__init__(http_url)
        self._metadata_cache: Dict[str, Dict] = {}

    async def get_metadata(self, token_address: str) -> Optional[Dict]:
        """
        Отримання метаданих токена.

        Args:
            token_address: Адреса токену

        Returns:
            Словник з метаданими або None
        """
        try:
            # Спочатку перевіряємо кеш
            if token_address in self._metadata_cache:
                return self._metadata_cache[token_address]

            # Отримуємо адресу метаданих
            metadata_address = await self._get_metadata_address(token_address)
            if not metadata_address:
                return None

            # Отримуємо дані метаданих
            result = await self._make_request(
                "getAccountInfo",
                [metadata_address, {"encoding": "jsonParsed"}]
            )

            if not result or 'data' not in result:
                return None

            # Парсимо метадані
            metadata = self._parse_metadata(result['data'])
            if metadata:
                self._metadata_cache[token_address] = metadata

            return metadata

        except Exception as e:
            logger.error(f"Помилка отримання метаданих для {token_address}: {e}")
            return None

    async def _get_metadata_address(self, token_address: str) -> Optional[str]:
        """
        Отримання адреси метаданих для токена.

        Args:
            token_address: Адреса токену

        Returns:
            Адреса метаданих або None
        """
        try:
            # Формуємо seed для PDA
            seeds = [
                b"metadata",
                bytes("metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s", "utf-8"),
                base58.b58decode(token_address)
            ]

            # Отримуємо PDA
            result = await self._make_request(
                "getProgramAccounts",
                [
                    "metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s",
                    {
                        "filters": [
                            {
                                "memcmp": {
                                    "offset": 32,
                                    "bytes": token_address
                                }
                            }
                        ]
                    }
                ]
            )

            if not result or not result['value']:
                return None

            return result['value'][0]['pubkey']

        except Exception as e:
            logger.error(f"Помилка отримання адреси метаданих для {token_address}: {e}")
            return None

    def _parse_metadata(self, data: Dict) -> Optional[Dict]:
        """
        Парсинг метаданих з відповіді API.

        Args:
            data: Дані метаданих

        Returns:
            Словник з розпарсеними метаданими або None
        """
        try:
            if 'parsed' not in data:
                return None

            parsed = data['parsed']
            return {
                'name': parsed.get('name', ''),
                'symbol': parsed.get('symbol', ''),
                'uri': parsed.get('uri', ''),
                'seller_fee_basis_points': parsed.get('sellerFeeBasisPoints', 0),
                'creators': parsed.get('creators', []),
                'verified': parsed.get('verified', False)
            }

        except Exception as e:
            logger.error(f"Помилка парсингу метаданих: {e}")
            return None

    def clear_cache(self, token_address: Optional[str] = None):
        """
        Очищення кешу метаданих.

        Args:
            token_address: Адреса токену для очищення або None для повного очищення
        """
        if token_address:
            self._metadata_cache.pop(token_address, None)
            logger.info(f"Кеш метаданих очищено для токену {token_address}")
        else:
            self._metadata_cache.clear()
            logger.info("Кеш метаданих повністю очищено") 