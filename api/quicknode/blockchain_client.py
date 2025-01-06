from typing import Dict, Optional, List, Any
import base64
from utils import get_logger
from utils.decorators import log_execution, measure_time
from .base import BaseQuickNodeClient, APIError
from .constants import (
    ErrorCode,
    DEFAULT_COMMITMENT,
    DEFAULT_TIMEOUT,
    DEFAULT_COMPUTE_UNIT_PRICE
)

logger = get_logger("quicknode_blockchain_client")

class BlockchainClient(BaseQuickNodeClient):
    """Клієнт для взаємодії з блокчейном через QuickNode"""
    
    def __init__(
        self,
        endpoint_manager=None,
        ssl_context=None,
        max_retries=None,
        retry_delay=None,
        default_commitment: str = DEFAULT_COMMITMENT,
        default_timeout: int = DEFAULT_TIMEOUT,
        compute_unit_price: int = DEFAULT_COMPUTE_UNIT_PRICE
    ):
        """
        Ініціалізація блокчейн клієнта
        
        Args:
            endpoint_manager: Менеджер ендпоінтів (опціонально)
            ssl_context: SSL контекст для захищених з'єднань
            max_retries: Максимальна кількість повторних спроб
            retry_delay: Затримка між спробами в секундах
            default_commitment: Рівень підтвердження за замовчуванням
            default_timeout: Таймаут за замовчуванням
            compute_unit_price: Ціна обчислювальних одиниць
        """
        super().__init__(
            endpoint_manager=endpoint_manager,
            ssl_context=ssl_context,
            max_retries=max_retries,
            retry_delay=retry_delay
        )
        self.default_commitment = default_commitment
        self.default_timeout = default_timeout
        self.compute_unit_price = compute_unit_price
        logger.info(
            f"BlockchainClient ініціалізовано з commitment={default_commitment}, "
            f"timeout={default_timeout}, compute_unit_price={compute_unit_price}"
        )
        
    @log_execution
    @measure_time
    async def send_transaction(
        self,
        transaction: str,
        commitment: Optional[str] = None
    ) -> str:
        """
        Відправка транзакції
        
        Args:
            transaction: Підписана транзакція в base64
            commitment: Рівень підтвердження
            
        Returns:
            str: Підпис транзакції
            
        Raises:
            APIError: Помилка API
            ValueError: Некоректні параметри
        """
        if not transaction:
            raise ValueError("Необхідно вказати транзакцію")
            
        commitment = commitment or self.default_commitment
        
        try:
            logger.info("Відправка транзакції")
            
            # Виконуємо запит
            response = await self._make_request(
                method="sendTransaction",
                params=[
                    transaction,
                    {
                        "encoding": "base64",
                        "commitment": commitment,
                        "computeUnitPrice": self.compute_unit_price
                    }
                ]
            )
            
            signature = response
            logger.info(f"Транзакцію відправлено: {signature}")
            
            return signature
            
        except APIError as e:
            logger.error(f"Помилка відправки транзакції: {str(e)}")
            raise
            
    @log_execution
    @measure_time
    async def get_latest_blockhash(
        self,
        commitment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Отримання останнього блокхешу
        
        Args:
            commitment: Рівень підтвердження
            
        Returns:
            Dict[str, Any]: Інформація про блокхеш
            
        Raises:
            APIError: Помилка API
        """
        commitment = commitment or self.default_commitment
        
        try:
            logger.info("Запит останнього блокхешу")
            
            # Виконуємо запит
            response = await self._make_request(
                method="getLatestBlockhash",
                params=[{"commitment": commitment}]
            )
            
            blockhash = response["value"]
            logger.info(f"Отримано блокхеш: {blockhash['blockhash']}")
            
            return blockhash
            
        except APIError as e:
            logger.error(f"Помилка отримання блокхешу: {str(e)}")
            raise
            
    @log_execution
    @measure_time
    async def get_account_info(
        self,
        address: str,
        commitment: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Отримання інформації про рахунок
        
        Args:
            address: Адреса рахунку
            commitment: Рівень підтвердження
            
        Returns:
            Optional[Dict[str, Any]]: Інформація про рахунок або None
            
        Raises:
            APIError: Помилка API
            ValueError: Некоректні параметри
        """
        if not address:
            raise ValueError("Необхідно вказати адресу рахунку")
            
        commitment = commitment or self.default_commitment
        
        try:
            logger.info(f"Запит інформації про рахунок {address}")
            
            # Виконуємо запит
            response = await self._make_request(
                method="getAccountInfo",
                params=[
                    address,
                    {
                        "encoding": "jsonParsed",
                        "commitment": commitment
                    }
                ]
            )
            
            if not response:
                logger.warning(f"Рахунок {address} не знайдено")
                return None
                
            account_info = response["value"]
            logger.info(f"Отримано інформацію про рахунок {address}")
            
            return account_info
            
        except APIError as e:
            logger.error(f"Помилка отримання інформації про рахунок {address}: {str(e)}")
            raise
            
    @log_execution
    @measure_time
    async def get_multiple_accounts(
        self,
        addresses: List[str],
        commitment: Optional[str] = None
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Отримання інформації про декілька рахунків
        
        Args:
            addresses: Список адрес
            commitment: Рівень підтвердження
            
        Returns:
            Dict[str, Optional[Dict[str, Any]]]: Словник інформації про рахунки
            
        Raises:
            APIError: Помилка API
            ValueError: Некоректні параметри
        """
        if not addresses:
            raise ValueError("Необхідно вказати список адрес")
            
        commitment = commitment or self.default_commitment
        
        try:
            logger.info(f"Запит інформації про {len(addresses)} рахунків")
            
            # Виконуємо запит
            response = await self._make_request(
                method="getMultipleAccounts",
                params=[
                    addresses,
                    {
                        "encoding": "jsonParsed",
                        "commitment": commitment
                    }
                ]
            )
            
            # Формуємо результат
            result = {}
            for i, account in enumerate(response["value"]):
                address = addresses[i]
                result[address] = account
                
            logger.info(f"Отримано інформацію про {len(result)} рахунків")
            return result
            
        except APIError as e:
            logger.error(f"Помилка отримання інформації про рахунки: {str(e)}")
            raise
            
    @log_execution
    @measure_time
    async def get_program_accounts(
        self,
        program_id: str,
        commitment: Optional[str] = None,
        filters: Optional[List[Dict]] = None,
        data_size: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Отримання рахунків програми
        
        Args:
            program_id: ID програми
            commitment: Рівень підтвердження
            filters: Фільтри для пошуку
            data_size: Розмір даних
            
        Returns:
            List[Dict[str, Any]]: Список рахунків
            
        Raises:
            APIError: Помилка API
            ValueError: Некоректні параметри
        """
        if not program_id:
            raise ValueError("Необхідно вказати ID програми")
            
        commitment = commitment or self.default_commitment
        
        try:
            logger.info(f"Запит рахунків програми {program_id}")
            
            # Формуємо конфігурацію
            config = {
                "encoding": "jsonParsed",
                "commitment": commitment
            }
            
            if filters:
                config["filters"] = filters
                
            if data_size is not None:
                config["dataSize"] = data_size
                
            # Виконуємо запит
            response = await self._make_request(
                method="getProgramAccounts",
                params=[program_id, config]
            )
            
            accounts = response
            logger.info(f"Отримано {len(accounts)} рахунків програми {program_id}")
            
            return accounts
            
        except APIError as e:
            logger.error(f"Помилка отримання рахунків програми {program_id}: {str(e)}")
            raise
