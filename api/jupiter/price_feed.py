from typing import Dict, Optional, List
from decimal import Decimal
from datetime import datetime, timedelta
from utils import get_logger
from utils.decorators import log_execution, measure_time
from .base import BaseJupiterClient, APIError
from .constants import (
    ErrorCode,
    PRICE_ENDPOINT_TYPE,
    PRICE_CACHE_TTL,
    DEFAULT_PRICE_AGE_THRESHOLD,
    WSOL_ADDRESS
)

logger = get_logger("jupiter_price_feed")

class PriceFeed(BaseJupiterClient):
    """Отримання цін з Jupiter API"""
    
    def __init__(
        self,
        endpoint_manager=None,
        ssl_context=None,
        max_retries=None,
        retry_delay=None,
        price_age_threshold: int = DEFAULT_PRICE_AGE_THRESHOLD
    ):
        """
        Ініціалізація фіду цін
        
        Args:
            endpoint_manager: Менеджер ендпоінтів (опціонально)
            ssl_context: SSL контекст для захищених з'єднань
            max_retries: Максимальна кількість повторних спроб
            retry_delay: Затримка між спробами в секундах
            price_age_threshold: Максимальний вік ціни в секундах
        """
        super().__init__(
            endpoint_manager=endpoint_manager,
            ssl_context=ssl_context,
            max_retries=max_retries,
            retry_delay=retry_delay
        )
        self.price_age_threshold = price_age_threshold
        self._price_cache = {}
        logger.info(
            f"PriceFeed ініціалізовано з price_age_threshold={price_age_threshold}"
        )
        
    @log_execution
    @measure_time
    async def get_price(
        self,
        token_address: str,
        vs_token: str = WSOL_ADDRESS,
        force_refresh: bool = False
    ) -> Optional[Decimal]:
        """
        Отримання ціни токена
        
        Args:
            token_address: Адреса токена
            vs_token: Адреса токена для порівняння
            force_refresh: Примусове оновлення ціни
            
        Returns:
            Optional[Decimal]: Ціна токена або None
            
        Raises:
            APIError: Помилка при отриманні ціни
            ValueError: Некоректні параметри
        """
        if not token_address:
            raise ValueError("Необхідно вказати адресу токена")
            
        cache_key = f"{token_address}_{vs_token}"
        
        # Перевіряємо кеш якщо не потрібне примусове оновлення
        if not force_refresh and cache_key in self._price_cache:
            price_data = self._price_cache[cache_key]
            age = (datetime.now() - price_data["timestamp"]).total_seconds()
            
            if age < PRICE_CACHE_TTL:
                logger.debug(
                    f"Використовуємо кешовану ціну для {token_address}: "
                    f"{price_data['price']}"
                )
                return price_data["price"]
                
        try:
            logger.info(f"Запит ціни для токена {token_address} vs {vs_token}")
            
            # Виконуємо запит
            response = await self._make_request(
                method="GET",
                endpoint_type=PRICE_ENDPOINT_TYPE,
                params={
                    "ids": token_address,
                    "vsToken": vs_token
                }
            )
            
            # Отримуємо ціну з відповіді
            price_data = response.get("data", {}).get(token_address)
            if not price_data:
                logger.warning(f"Не знайдено ціну для токена {token_address}")
                return None
                
            # Перевіряємо вік ціни
            price_age = int(price_data.get("age", 0))
            if price_age > self.price_age_threshold:
                logger.warning(
                    f"Ціна для {token_address} застаріла "
                    f"(вік: {price_age} сек)"
                )
                return None
                
            # Конвертуємо ціну
            price = Decimal(str(price_data["price"]))
            
            # Зберігаємо в кеш
            self._price_cache[cache_key] = {
                "price": price,
                "timestamp": datetime.now()
            }
            
            logger.info(f"Отримано ціну для {token_address}: {price}")
            return price
            
        except APIError as e:
            logger.error(f"Помилка отримання ціни для {token_address}: {str(e)}")
            raise
            
    @log_execution
    async def get_price_history(
        self,
        token_address: str,
        vs_token: str = WSOL_ADDRESS,
        interval: str = "1h",
        limit: int = 24
    ) -> List[Dict]:
        """
        Отримання історії цін токена
        
        Args:
            token_address: Адреса токена
            vs_token: Адреса токена для порівняння
            interval: Інтервал ('5m', '15m', '1h', '4h', '1d')
            limit: Кількість точок даних
            
        Returns:
            List[Dict]: Історія цін
            
        Raises:
            APIError: Помилка при отриманні історії
            ValueError: Некоректні параметри
        """
        if not token_address:
            raise ValueError("Необхідно вказати адресу токена")
            
        if interval not in ["5m", "15m", "1h", "4h", "1d"]:
            raise ValueError("Некоректний інтервал")
            
        try:
            logger.info(
                f"Запит історії цін для {token_address} "
                f"(інтервал: {interval}, ліміт: {limit})"
            )
            
            # Виконуємо запит
            response = await self._make_request(
                method="GET",
                endpoint_type=PRICE_ENDPOINT_TYPE,
                path="history",
                params={
                    "id": token_address,
                    "vsToken": vs_token,
                    "interval": interval,
                    "limit": limit
                }
            )
            
            history = response.get("data", [])
            logger.info(f"Отримано {len(history)} точок даних")
            
            return history
            
        except APIError as e:
            logger.error(
                f"Помилка отримання історії цін для {token_address}: {str(e)}"
            )
            raise
            
    @log_execution
    async def get_price_impact(
        self,
        token_address: str,
        amount: Decimal,
        vs_token: str = WSOL_ADDRESS
    ) -> Optional[Decimal]:
        """
        Розрахунок впливу на ціну для заданої суми
        
        Args:
            token_address: Адреса токена
            amount: Сума в токенах
            vs_token: Адреса токена для порівняння
            
        Returns:
            Optional[Decimal]: Вплив на ціну у відсотках або None
            
        Raises:
            APIError: Помилка при розрахунку
            ValueError: Некоректні параметри
        """
        if not token_address or amount <= 0:
            raise ValueError("Некоректні параметри")
            
        try:
            logger.info(
                f"Розрахунок впливу на ціну для {token_address} "
                f"(сума: {amount})"
            )
            
            # Виконуємо запит
            response = await self._make_request(
                method="GET",
                endpoint_type=PRICE_ENDPOINT_TYPE,
                path="impact",
                params={
                    "id": token_address,
                    "vsToken": vs_token,
                    "amount": str(amount)
                }
            )
            
            impact = Decimal(str(response.get("priceImpact", 0)))
            logger.info(f"Розрахований вплив на ціну: {impact}%")
            
            return impact
            
        except APIError as e:
            logger.error(
                f"Помилка розрахунку впливу на ціну для {token_address}: {str(e)}"
            )
            raise
