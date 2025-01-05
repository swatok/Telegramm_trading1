from typing import Dict, Optional, List
from decimal import Decimal
from utils import get_logger
from utils.decorators import log_execution, measure_time
from .base import BaseJupiterClient, APIError
from .constants import (
    ErrorCode,
    SWAP_ENDPOINT_TYPE,
    DEFAULT_SLIPPAGE,
    DEFAULT_TIMEOUT,
    WSOL_ADDRESS,
    TransactionStatus
)

logger = get_logger("jupiter_swap_executor")

class SwapExecutor(BaseJupiterClient):
    """Виконання свопів через Jupiter API"""
    
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
        Ініціалізація виконавця свопів
        
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
            f"SwapExecutor ініціалізовано з default_slippage={default_slippage}, "
            f"default_timeout={default_timeout}"
        )
        
    @log_execution
    @measure_time
    async def get_quote(
        self,
        input_token: str,
        output_token: str,
        amount: Decimal,
        slippage: Optional[Decimal] = None
    ) -> Dict:
        """
        Отримання котирування для свопу
        
        Args:
            input_token: Адреса вхідного токена
            output_token: Адреса вихідного токена
            amount: Сума в токенах
            slippage: Максимальний проковз в процентах
            
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
                f"Запит котирування для свопу {input_token} -> {output_token} "
                f"(сума: {amount}, проковз: {slippage}%)"
            )
            
            # Виконуємо запит
            response = await self._make_request(
                method="GET",
                endpoint_type=SWAP_ENDPOINT_TYPE,
                path="quote",
                params={
                    "inputMint": input_token,
                    "outputMint": output_token,
                    "amount": str(amount),
                    "slippage": str(slippage)
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
    @measure_time
    async def prepare_swap(
        self,
        quote_response: Dict,
        user_public_key: str
    ) -> Dict:
        """
        Підготовка транзакції свопу
        
        Args:
            quote_response: Відповідь від quote API
            user_public_key: Публічний ключ користувача
            
        Returns:
            Dict: Підготовлена транзакція
            
        Raises:
            APIError: Помилка при підготовці транзакції
            ValueError: Некоректні параметри
        """
        if not quote_response or not user_public_key:
            raise ValueError("Некоректні параметри")
            
        try:
            logger.info(f"Підготовка транзакції свопу для {user_public_key}")
            
            # Виконуємо запит
            response = await self._make_request(
                method="POST",
                endpoint_type=SWAP_ENDPOINT_TYPE,
                path="prepare",
                json={
                    "quoteResponse": quote_response,
                    "userPublicKey": user_public_key
                }
            )
            
            logger.info(f"Транзакція підготовлена: {response['txid']}")
            return response
            
        except APIError as e:
            logger.error(f"Помилка підготовки транзакції: {str(e)}")
            raise
            
    @log_execution
    @measure_time
    async def execute_swap(
        self,
        prepared_transaction: Dict,
        signature: str
    ) -> Dict:
        """
        Виконання підготовленої транзакції свопу
        
        Args:
            prepared_transaction: Підготовлена транзакція
            signature: Підпис транзакції
            
        Returns:
            Dict: Результат виконання
            
        Raises:
            APIError: Помилка при виконанні
            ValueError: Некоректні параметри
        """
        if not prepared_transaction or not signature:
            raise ValueError("Некоректні параметри")
            
        try:
            logger.info(f"Виконання транзакції свопу {prepared_transaction['txid']}")
            
            # Виконуємо запит
            response = await self._make_request(
                method="POST",
                endpoint_type=SWAP_ENDPOINT_TYPE,
                path="execute",
                json={
                    "preparedTransaction": prepared_transaction,
                    "signature": signature
                }
            )
            
            status = response.get("status")
            if status == TransactionStatus.SUCCESS:
                logger.info(f"Своп успішно виконано: {response['txid']}")
            else:
                logger.warning(
                    f"Своп завершився зі статусом {status}: {response['txid']}"
                )
                
            return response
            
        except APIError as e:
            logger.error(f"Помилка виконання свопу: {str(e)}")
            raise
            
    @log_execution
    async def get_transaction_status(self, txid: str) -> Dict:
        """
        Отримання статусу транзакції
        
        Args:
            txid: ID транзакції
            
        Returns:
            Dict: Статус транзакції
            
        Raises:
            APIError: Помилка при отриманні статусу
            ValueError: Некоректний ID транзакції
        """
        if not txid:
            raise ValueError("Необхідно вказати ID транзакції")
            
        try:
            logger.info(f"Запит статусу транзакції {txid}")
            
            # Виконуємо запит
            response = await self._make_request(
                method="GET",
                endpoint_type=SWAP_ENDPOINT_TYPE,
                path=f"transaction/{txid}"
            )
            
            status = response.get("status")
            logger.info(f"Отримано статус транзакції {txid}: {status}")
            
            return response
            
        except APIError as e:
            logger.error(f"Помилка отримання статусу транзакції {txid}: {str(e)}")
            raise
