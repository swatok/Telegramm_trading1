"""
Модуль для валідації токенів.
Відповідає за перевірку токенів на відповідність критеріям торгівлі.
"""

from decimal import Decimal
from typing import Dict, Optional, List
import re

from .constants import LIQUIDITY_MIN, TRANSACTION_MIN
from ..api.jupiter import JupiterApi
from ..api.quicknode import TokenManager
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class TokenValidator:
    """
    Клас для валідації токенів.
    Перевіряє токени на відповідність критеріям безпеки та торгівлі.
    """

    def __init__(self, jupiter_api: JupiterApi, quicknode_url: str):
        """
        Ініціалізація валідатора токенів.

        Args:
            jupiter_api: Екземпляр API Jupiter
            quicknode_url: URL для HTTP запитів до QuickNode
        """
        self.jupiter_api = jupiter_api
        self.token_manager = TokenManager(quicknode_url)
        self._blacklisted_tokens: List[str] = []
        self._validated_tokens: Dict[str, Dict] = {}

    async def validate_token(self, token_address: str) -> Dict[str, bool]:
        """
        Комплексна валідація токену.

        Args:
            token_address: Адреса токену

        Returns:
            Словник з результатами перевірок
        """
        if token_address in self._blacklisted_tokens:
            return {'valid': False, 'reason': 'Token is blacklisted'}

        if token_address in self._validated_tokens:
            return self._validated_tokens[token_address]

        results = {
            'valid': True,
            'checks': {
                'address_valid': False,
                'exists_on_chain': False,
                'has_liquidity': False,
                'has_volume': False,
                'contract_verified': False,
                'not_honeypot': False
            }
        }

        try:
            # Перевірка формату адреси
            results['checks']['address_valid'] = self._validate_address_format(token_address)
            if not results['checks']['address_valid']:
                results['valid'] = False
                results['reason'] = 'Invalid address format'
                return results

            # Перевірка існування токена в мережі
            token_info = await self.token_manager.verify_token(token_address)
            results['checks']['exists_on_chain'] = token_info is not None
            if not results['checks']['exists_on_chain']:
                results['valid'] = False
                results['reason'] = 'Token does not exist on chain'
                return results

            # Перевірка ліквідності
            liquidity = await self._check_liquidity(token_address)
            results['checks']['has_liquidity'] = liquidity >= LIQUIDITY_MIN
            if not results['checks']['has_liquidity']:
                results['valid'] = False
                results['reason'] = 'Insufficient liquidity'
                return results

            # Перевірка об'єму торгів
            volume = await self._check_volume(token_address)
            results['checks']['has_volume'] = volume >= TRANSACTION_MIN
            if not results['checks']['has_volume']:
                results['valid'] = False
                results['reason'] = 'Insufficient trading volume'
                return results

            # Перевірка контракту
            contract_check = await self._validate_contract(token_address)
            results['checks']['contract_verified'] = contract_check['verified']
            results['checks']['not_honeypot'] = contract_check['not_honeypot']
            
            if not contract_check['verified'] or not contract_check['not_honeypot']:
                results['valid'] = False
                results['reason'] = 'Contract validation failed'
                return results

            self._validated_tokens[token_address] = results
            return results

        except Exception as e:
            logger.error(f"Помилка валідації токену {token_address}: {e}")
            results['valid'] = False
            results['reason'] = f"Validation error: {str(e)}"
            return results

    def _validate_address_format(self, address: str) -> bool:
        """
        Перевірка формату адреси токену.

        Args:
            address: Адреса токену

        Returns:
            True якщо формат правильний, False інакше
        """
        if not address:
            return False
        # Перевірка формату адреси Solana
        return bool(re.match(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$', address))

    async def _check_liquidity(self, token_address: str) -> Decimal:
        """
        Перевірка ліквідності токену.

        Args:
            token_address: Адреса токену

        Returns:
            Значення ліквідності
        """
        try:
            pool_info = await self.jupiter_api.get_pool_info(token_address)
            return Decimal(str(pool_info.get('liquidity', 0)))
        except Exception as e:
            logger.error(f"Помилка перевірки ліквідності {token_address}: {e}")
            return Decimal('0')

    async def _check_volume(self, token_address: str) -> Decimal:
        """
        Перевірка об'єму торгів токену.

        Args:
            token_address: Адреса токену

        Returns:
            Значення об'єму торгів
        """
        try:
            volume_data = await self.jupiter_api.get_token_volume(token_address)
            return Decimal(str(volume_data.get('volume_24h', 0)))
        except Exception as e:
            logger.error(f"Помилка перевірки об'єму {token_address}: {e}")
            return Decimal('0')

    async def _validate_contract(self, token_address: str) -> Dict[str, bool]:
        """
        Валідація смарт-контракту токену.

        Args:
            token_address: Адреса токену

        Returns:
            Словник з результатами перевірки контракту
        """
        try:
            contract_data = await self.jupiter_api.get_token_info(token_address)
            return {
                'verified': contract_data.get('verified', False),
                'not_honeypot': not contract_data.get('is_honeypot', True)
            }
        except Exception as e:
            logger.error(f"Помилка валідації контракту {token_address}: {e}")
            return {'verified': False, 'not_honeypot': False}

    def add_to_blacklist(self, token_address: str):
        """
        Додавання токену до чорного списку.

        Args:
            token_address: Адреса токену
        """
        if token_address not in self._blacklisted_tokens:
            self._blacklisted_tokens.append(token_address)
            if token_address in self._validated_tokens:
                del self._validated_tokens[token_address]
            logger.info(f"Токен {token_address} додано до чорного списку")

    def remove_from_blacklist(self, token_address: str):
        """
        Видалення токену з чорного списку.

        Args:
            token_address: Адреса токену
        """
        if token_address in self._blacklisted_tokens:
            self._blacklisted_tokens.remove(token_address)
            logger.info(f"Токен {token_address} видалено з чорного списку")

    def is_blacklisted(self, token_address: str) -> bool:
        """
        Перевірка чи токен у чорному списку.

        Args:
            token_address: Адреса токену

        Returns:
            True якщо токен у чорному списку, False інакше
        """
        return token_address in self._blacklisted_tokens

    def clear_validation_cache(self, token_address: Optional[str] = None):
        """
        Очищення кешу валідації.

        Args:
            token_address: Адреса токену для очищення або None для повного очищення
        """
        if token_address:
            self._validated_tokens.pop(token_address, None)
            logger.info(f"Кеш валідації очищено для токену {token_address}")
        else:
            self._validated_tokens.clear()
            logger.info("Кеш валідації повністю очищено") 