# quote_manager.py
from typing import Dict, Optional, List
from decimal import Decimal
from utils import get_logger
from utils.decorators import log_execution, measure_time
from .base import BaseJupiterClient, APIError
from .constants import (
    ErrorCode,
    QUOTE_ENDPOINT_TYPE,
    DEFAULT_SLIPPAGE,
    DEFAULT_TIMEOUT,
    WSOL_ADDRESS
)

logger = get_logger("jupiter_quote_manager")

class QuoteManager(BaseJupiterClient):
    """Менеджер котирувань Jupiter API"""
    
    def __init__(
        self,
        endpoint_manager=None,
        ssl_context=None,
        max_retries=None,
        retry_delay=None,
        default_slippage: Decimal = DEFAULT_SLIPPAGE,
        default_timeout: int = DEFAULT_TIMEOUT
    ):
        """
        Ініціалізація менеджера котирувань
        
        Args:
            endpoint_manager: Менеджер ендпоінтів (опціонально)
            ssl_context: SSL контекст для захищених з'єднань
            max_retries: Максимальна кількість повторних спроб
            retry_delay: Затримка між спробами в секундах
            default_slippage: Дефолтний проковз в процентах
            default_timeout: Дефолтний таймаут в секундах
        """
        super().__init__(
            endpoint_manager=endpoint_manager,
            ssl_context=ssl_context,
            max_retries=max_retries,
            retry_delay=retry_delay
        )
        self.default_slippage = default_slippage
        self.default_timeout = default_timeout
        logger.info(
            f"QuoteManager ініціалізовано з default_slippage={default_slippage}, "
            f"default_timeout={default_timeout}"
        )
        
    @log_execution
    @measure_time
    async def get_quote(
        self,
        input_token: str,
        output_token: str,
        amount: Decimal,
        slippage: Optional[Decimal] = None,
        only_direct_routes: bool = False
    ) -> Dict:
        """
        Отримання котирування для обміну
        
        Args:
            input_token: Адреса вхідного токена
            output_token: Адреса вихідного токена
            amount: Сума в токенах
            slippage: Максимальний проковз в процентах
            only_direct_routes: Використовувати тільки прямі маршрути
            
        Returns:
            Dict: Інформація про котирування
            
        Raises:
            APIError: Помилка при отриманні котирування
            ValueError: Некоректні параметри
        """
        if not input_token or not output_token or amount <= 0:
            raise ValueError("Некоректні параметри")
            
        slippage = slippage or self.default_slippage
        
        try:
            logger.info(
                f"Запит котирування для {input_token} -> {output_token} "
                f"(сума: {amount}, проковз: {slippage}%)"
            )
            
            # Виконуємо запит
            response = await self._make_request(
                method="GET",
                endpoint_type=QUOTE_ENDPOINT_TYPE,
                params={
                    "inputMint": input_token,
                    "outputMint": output_token,
                    "amount": str(amount),
                    "slippage": str(slippage),
                    "onlyDirectRoutes": only_direct_routes
                }
            )
            
            logger.info(
                f"Отримано котирування: вхід={response['inAmount']}, "
                f"вихід={response['outAmount']}"
            )
            return response
            
        except APIError as e:
            logger.error(
                f"Помилка отримання котирування для {input_token}->{output_token}: "
                f"{str(e)}"
            )
            raise
            
    @log_execution
    async def get_best_route(
        self,
        input_token: str,
        output_token: str,
        amount: Decimal,
        slippage: Optional[Decimal] = None
    ) -> Optional[Dict]:
        """
        Пошук найкращого маршруту для обміну
        
        Args:
            input_token: Адреса вхідного токена
            output_token: Адреса вихідного токена
            amount: Сума в токенах
            slippage: Максимальний проковз в процентах
            
        Returns:
            Optional[Dict]: Найкращий маршрут або None
            
        Raises:
            APIError: Помилка при пошуку маршруту
            ValueError: Некоректні параметри
        """
        if not input_token or not output_token or amount <= 0:
            raise ValueError("Некоректні параметри")
            
        slippage = slippage or self.default_slippage
        
        try:
            logger.info(
                f"Пошук найкращого маршруту для {input_token} -> {output_token} "
                f"(сума: {amount})"
            )
            
            # Отримуємо котирування з усіма маршрутами
            quote = await self.get_quote(
                input_token=input_token,
                output_token=output_token,
                amount=amount,
                slippage=slippage,
                only_direct_routes=False
            )
            
            # Знаходимо маршрут з найкращою ціною
            routes = quote.get("routes", [])
            if not routes:
                logger.warning("Не знайдено жодного маршруту")
                return None
                
            best_route = max(
                routes,
                key=lambda r: Decimal(str(r["outAmount"]))
            )
            
            logger.info(
                f"Знайдено найкращий маршрут: "
                f"вхід={best_route['inAmount']}, "
                f"вихід={best_route['outAmount']}"
            )
            return best_route
            
        except APIError as e:
            logger.error(
                f"Помилка пошуку маршруту для {input_token}->{output_token}: "
                f"{str(e)}"
            )
            raise
            
    @log_execution
    async def get_price_impact(
        self,
        input_token: str,
        output_token: str,
        amount: Decimal
    ) -> Optional[Decimal]:
        """
        Розрахунок впливу на ціну для заданої суми
        
        Args:
            input_token: Адреса вхідного токена
            output_token: Адреса вихідного токена
            amount: Сума в токенах
            
        Returns:
            Optional[Decimal]: Вплив на ціну у відсотках або None
            
        Raises:
            APIError: Помилка при розрахунку
            ValueError: Некоректні параметри
        """
        if not input_token or not output_token or amount <= 0:
            raise ValueError("Некоректні параметри")
            
        try:
            logger.info(
                f"Розрахунок впливу на ціну для {input_token} -> {output_token} "
                f"(сума: {amount})"
            )
            
            # Отримуємо котирування
            quote = await self.get_quote(
                input_token=input_token,
                output_token=output_token,
                amount=amount
            )
            
            impact = Decimal(str(quote.get("priceImpact", 0)))
            logger.info(f"Розрахований вплив на ціну: {impact}%")
            
            return impact
            
        except APIError as e:
            logger.error(
                f"Помилка розрахунку впливу на ціну для "
                f"{input_token}->{output_token}: {str(e)}"
            )
            raise