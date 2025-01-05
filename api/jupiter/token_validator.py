from typing import Dict, Optional, List
from decimal import Decimal
from utils import get_logger
from utils.decorators import log_execution, measure_time
from .base import BaseJupiterClient, APIError
from .constants import (
    ErrorCode,
    TOKEN_LIST_ENDPOINT_TYPE,
    MIN_LIQUIDITY_THRESHOLD,
    TOKEN_CACHE_TTL,
    WSOL_ADDRESS
)

logger = get_logger("jupiter_token_validator")

class TokenValidator(BaseJupiterClient):
    """Валідатор токенів Jupiter API"""
    
    def __init__(
        self,
        endpoint_manager=None,
        ssl_context=None,
        max_retries=None,
        retry_delay=None,
        min_liquidity: Decimal = MIN_LIQUIDITY_THRESHOLD
    ):
        """
        Ініціалізація валідатора токенів
        
        Args:
            endpoint_manager: Менеджер ендпоінтів (опціонально)
            ssl_context: SSL контекст для захищених з'єднань
            max_retries: Максимальна кількість повторних спроб
            retry_delay: Затримка між спробами в секундах
            min_liquidity: Мінімальний поріг ліквідності
        """
        super().__init__(
            endpoint_manager=endpoint_manager,
            ssl_context=ssl_context,
            max_retries=max_retries,
            retry_delay=retry_delay
        )
        self.min_liquidity = min_liquidity
        self._token_cache = {}
        logger.info(
            f"TokenValidator ініціалізовано з min_liquidity={min_liquidity}"
        )
        
    @log_execution
    @measure_time
    async def get_token_info(self, token_address: str) -> Optional[Dict]:
        """
        Отримання інформації про токен
        
        Args:
            token_address: Адреса токена
            
        Returns:
            Optional[Dict]: Інформація про токен або None
            
        Raises:
            APIError: Помилка при отриманні інформації
            ValueError: Некоректна адреса токена
        """
        if not token_address:
            raise ValueError("Необхідно вказати адресу токена")
            
        # Перевіряємо кеш
        if token_address in self._token_cache:
            logger.debug(f"Знайдено токен {token_address} в кеші")
            return self._token_cache[token_address]
            
        try:
            logger.info(f"Запит інформації про токен {token_address}")
            
            # Виконуємо запит
            response = await self._make_request(
                method="GET",
                endpoint_type=TOKEN_LIST_ENDPOINT_TYPE,
                path=f"token/{token_address}"
            )
            
            # Зберігаємо в кеш
            self._token_cache[token_address] = response
            
            logger.info(f"Отримано інформацію про токен {token_address}")
            return response
            
        except APIError as e:
            if "not found" in str(e).lower():
                logger.warning(f"Токен {token_address} не знайдено")
                return None
            raise
            
    @log_execution
    async def validate_token(
        self,
        token_address: str,
        check_liquidity: bool = True
    ) -> bool:
        """
        Перевірка валідності токена
        
        Args:
            token_address: Адреса токена
            check_liquidity: Перевіряти ліквідність
            
        Returns:
            bool: True якщо токен валідний
            
        Raises:
            APIError: Помилка при перевірці
        """
        try:
            # Отримуємо інформацію про токен
            token_info = await self.get_token_info(token_address)
            
            if not token_info:
                logger.warning(f"Токен {token_address} не знайдено")
                return False
                
            # Перевіряємо базові параметри
            if not all([
                token_info.get("address"),
                token_info.get("decimals"),
                token_info.get("symbol")
            ]):
                logger.warning(
                    f"Токен {token_address} не має необхідних параметрів"
                )
                return False
                
            # Перевіряємо ліквідність якщо потрібно
            if check_liquidity:
                liquidity = Decimal(str(token_info.get("liquidity", 0)))
                if liquidity < self.min_liquidity:
                    logger.warning(
                        f"Ліквідність токена {token_address} "
                        f"({liquidity}) нижче порогу {self.min_liquidity}"
                    )
                    return False
                    
            logger.info(f"Токен {token_address} успішно пройшов валідацію")
            return True
            
        except APIError as e:
            logger.error(f"Помилка валідації токена {token_address}: {str(e)}")
            raise
            
    @log_execution
    async def check_pair_tradable(
        self,
        input_token: str,
        output_token: str
    ) -> bool:
        """
        Перевірка можливості торгівлі пари токенів
        
        Args:
            input_token: Адреса вхідного токена
            output_token: Адреса вихідного токена
            
        Returns:
            bool: True якщо пара торгується
            
        Raises:
            APIError: Помилка при перевірці
        """
        try:
            # Перевіряємо обидва токени
            input_valid = await self.validate_token(input_token)
            output_valid = await self.validate_token(output_token)
            
            if not (input_valid and output_valid):
                logger.warning(
                    f"Пара {input_token}/{output_token} не валідна: "
                    f"input_valid={input_valid}, output_valid={output_valid}"
                )
                return False
                
            # Перевіряємо наявність маршруту
            params = {
                "inputMint": input_token,
                "outputMint": output_token
            }
            
            try:
                await self._make_request(
                    method="GET",
                    endpoint_type=TOKEN_LIST_ENDPOINT_TYPE,
                    path="route-map",
                    params=params
                )
                logger.info(f"Знайдено маршрут для пари {input_token}/{output_token}")
                return True
                
            except APIError as e:
                if "no route" in str(e).lower():
                    logger.warning(
                        f"Не знайдено маршрут для пари {input_token}/{output_token}"
                    )
                    return False
                raise
                
        except APIError as e:
            logger.error(
                f"Помилка перевірки пари {input_token}/{output_token}: {str(e)}"
            )
            raise
            
    @log_execution
    async def get_token_list(self, include_unverified: bool = False) -> List[Dict]:
        """
        Отримання списку всіх токенів
        
        Args:
            include_unverified: Включати неверифіковані токени
            
        Returns:
            List[Dict]: Список токенів
            
        Raises:
            APIError: Помилка при отриманні списку
        """
        try:
            logger.info("Запит списку токенів")
            
            # Виконуємо запит
            response = await self._make_request(
                method="GET",
                endpoint_type=TOKEN_LIST_ENDPOINT_TYPE,
                path="all",
                params={"includeUnverified": include_unverified}
            )
            
            tokens = response.get("tokens", [])
            logger.info(f"Отримано {len(tokens)} токенів")
            
            return tokens
            
        except APIError as e:
            logger.error(f"Помилка отримання списку токенів: {str(e)}")
            raise
