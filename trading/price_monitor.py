"""
Модуль для моніторингу цін.
Відповідає за отримання та відстеження цін токенів.
"""

from decimal import Decimal
from typing import Dict, Optional
import asyncio
from datetime import datetime

from .constants import LIQUIDITY_MIN
from ..api.jupiter import JupiterApi
from ..api.quicknode import PriceMonitor as QuickNodePriceMonitor
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class PriceMonitor:
    """
    Клас для моніторингу цін токенів.
    Реалізує патерн Observer для сповіщення про зміни цін.
    """

    def __init__(self, jupiter_api: JupiterApi, quicknode_ws_url: str):
        """
        Ініціалізація монітора цін.

        Args:
            jupiter_api: Екземпляр API Jupiter для отримання цін
            quicknode_ws_url: URL для WebSocket підключення до QuickNode
        """
        self.jupiter_api = jupiter_api
        self._price_cache: Dict[str, Dict] = {}
        self._observers = []
        self._monitoring = False
        self._quicknode_monitor = None

    async def start_monitoring(self, token_address: str, interval: int = 60):
        """
        Запуск моніторингу ціни для конкретного токену.

        Args:
            token_address: Адреса токену для моніторингу
            interval: Інтервал оновлення в секундах
        """
        self._monitoring = True
        
        # Створюємо QuickNode монітор
        self._quicknode_monitor = QuickNodePriceMonitor(
            self.quicknode_ws_url,
            [token_address],
            self._handle_quicknode_update
        )
        
        # Запускаємо обидва моніторинги
        await asyncio.gather(
            self._monitor_jupiter_price(token_address, interval),
            self._quicknode_monitor.start()
        )

    async def stop_monitoring(self):
        """Зупинка моніторингу цін."""
        self._monitoring = False
        if self._quicknode_monitor:
            await self._quicknode_monitor.stop()

    async def _monitor_jupiter_price(self, token_address: str, interval: int):
        """
        Моніторинг ціни через Jupiter.

        Args:
            token_address: Адреса токену
            interval: Інтервал оновлення
        """
        while self._monitoring:
            try:
                await self._update_price(token_address)
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Помилка при моніторингу ціни через Jupiter: {e}")
                await asyncio.sleep(5)

    async def _handle_quicknode_update(self, token_data: Dict):
        """
        Обробка оновлень від QuickNode.

        Args:
            token_data: Дані про токен
        """
        try:
            if 'price' in token_data:
                token_address = token_data.get('address')
                old_price = self._price_cache.get(token_address, {}).get('price')
                
                self._price_cache[token_address] = {
                    'price': Decimal(str(token_data['price'])),
                    'liquidity': Decimal(str(token_data.get('liquidity', 0))),
                    'timestamp': datetime.now(),
                    'source': 'quicknode'
                }
                
                # Сповіщаємо про зміну ціни
                if old_price is not None:
                    for observer in self._observers:
                        await observer.on_price_change(
                            token_address,
                            old_price,
                            self._price_cache[token_address]
                        )
                        
        except Exception as e:
            logger.error(f"Помилка обробки оновлення від QuickNode: {e}")

    async def _update_price(self, token_address: str):
        """
        Оновлення ціни токену через Jupiter.

        Args:
            token_address: Адреса токену
        """
        price_data = await self.jupiter_api.get_price(token_address)
        if not price_data:
            return

        old_price = self._price_cache.get(token_address, {}).get('price')
        self._price_cache[token_address] = {
            'price': Decimal(str(price_data['price'])),
            'liquidity': Decimal(str(price_data.get('liquidity', 0))),
            'timestamp': datetime.now(),
            'source': 'jupiter'
        }

        # Сповіщення спостерігачів про зміну ціни
        if old_price is not None:
            for observer in self._observers:
                await observer.on_price_change(
                    token_address,
                    old_price,
                    self._price_cache[token_address]
                )

    def add_observer(self, observer):
        """
        Додавання спостерігача за зміною цін.

        Args:
            observer: Об'єкт спостерігача з методом on_price_change
        """
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer):
        """
        Видалення спостерігача.

        Args:
            observer: Об'єкт спостерігача для видалення
        """
        if observer in self._observers:
            self._observers.remove(observer)

    def get_current_price(self, token_address: str) -> Optional[Dict]:
        """
        Отримання поточної ціни токену.

        Args:
            token_address: Адреса токену

        Returns:
            Dict з інформацією про ціну або None
        """
        return self._price_cache.get(token_address)

    def has_sufficient_liquidity(self, token_address: str) -> bool:
        """
        Перевірка достатності ліквідності.

        Args:
            token_address: Адреса токену

        Returns:
            True якщо ліквідність достатня, False інакше
        """
        price_data = self._price_cache.get(token_address)
        if not price_data:
            return False
        return price_data['liquidity'] >= LIQUIDITY_MIN 