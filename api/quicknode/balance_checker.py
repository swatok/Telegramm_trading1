from typing import Dict, Optional, List
import asyncio
from utils import get_logger
from utils.decorators import log_execution, measure_time
from .base import BaseQuickNodeClient, APIError
from .constants import (
    ErrorCode,
    DEFAULT_COMMITMENT,
    DEFAULT_TIMEOUT,
    TOKEN_PROGRAM_ID
)

logger = get_logger("quicknode_balance_checker")

class BalanceChecker(BaseQuickNodeClient):
    """Перевірка балансів через QuickNode"""
    
    def __init__(
        self,
        endpoint_manager=None,
        ssl_context=None,
        max_retries=None,
        retry_delay=None,
        default_commitment: str = DEFAULT_COMMITMENT,
        default_timeout: int = DEFAULT_TIMEOUT
    ):
        """
        Ініціалізація перевірки балансів
        
        Args:
            endpoint_manager: Менеджер ендпоінтів (опціонально)
            ssl_context: SSL контекст для захищених з'єднань
            max_retries: Максимальна кількість повторних спроб
            retry_delay: Затримка між спробами в секундах
            default_commitment: Рівень підтвердження за замовчуванням
            default_timeout: Таймаут за замовчуванням
        """
        super().__init__(
            endpoint_manager=endpoint_manager,
            ssl_context=ssl_context,
            max_retries=max_retries,
            retry_delay=retry_delay
        )
        self.default_commitment = default_commitment
        self.default_timeout = default_timeout
        logger.info(
            f"BalanceChecker ініціалізовано з commitment={default_commitment}, "
            f"timeout={default_timeout}"
        )
        
    @log_execution
    @measure_time
    async def get_sol_balance(
        self,
        address: str,
        commitment: Optional[str] = None
    ) -> float:
        """
        Отримання балансу SOL
        
        Args:
            address: Адреса гаманця
            commitment: Рівень підтвердження
            
        Returns:
            float: Баланс в SOL
            
        Raises:
            APIError: Помилка API
            ValueError: Некоректні параметри
        """
        if not address:
            raise ValueError("Необхідно вказати адресу гаманця")
            
        commitment = commitment or self.default_commitment
        
        try:
            logger.info(f"Запит балансу SOL для {address}")
            
            # Виконуємо запит
            response = await self._make_request(
                method="getBalance",
                params=[
                    address,
                    {"commitment": commitment}
                ]
            )
            
            # Конвертуємо в SOL
            balance = float(response) / 1e9
            logger.info(f"Баланс SOL для {address}: {balance}")
            
            return balance
            
        except APIError as e:
            logger.error(f"Помилка отримання балансу SOL для {address}: {str(e)}")
            raise
            
    @log_execution
    @measure_time
    async def get_token_balance(
        self,
        address: str,
        token_mint: str,
        commitment: Optional[str] = None
    ) -> float:
        """
        Отримання балансу токена
        
        Args:
            address: Адреса гаманця
            token_mint: Адреса токена
            commitment: Рівень підтвердження
            
        Returns:
            float: Баланс токена
            
        Raises:
            APIError: Помилка API
            ValueError: Некоректні параметри
        """
        if not address:
            raise ValueError("Необхідно вказати адресу гаманця")
            
        if not token_mint:
            raise ValueError("Необхідно вказати адресу токена")
            
        commitment = commitment or self.default_commitment
        
        try:
            logger.info(f"Запит балансу {token_mint} для {address}")
            
            # Отримуємо токен-акаунт
            token_account = await self._get_token_account(
                address,
                token_mint,
                commitment
            )
            
            if not token_account:
                # Якщо акаунт не існує - баланс 0
                logger.info(f"Токен-акаунт для {token_mint} не знайдено")
                return 0.0
                
            # Отримуємо баланс
            response = await self._make_request(
                method="getTokenAccountBalance",
                params=[
                    token_account,
                    {"commitment": commitment}
                ]
            )
            
            # Парсимо результат
            amount = float(response["amount"])
            decimals = response["decimals"]
            balance = amount / (10 ** decimals)
            
            logger.info(f"Баланс {token_mint} для {address}: {balance}")
            return balance
            
        except APIError as e:
            logger.error(
                f"Помилка отримання балансу {token_mint} для {address}: {str(e)}"
            )
            raise
            
    @log_execution
    async def check_sufficient_balance(
        self,
        address: str,
        required_sol: float,
        required_tokens: Optional[Dict[str, float]] = None,
        commitment: Optional[str] = None
    ) -> bool:
        """
        Перевірка достатності балансів
        
        Args:
            address: Адреса гаманця
            required_sol: Необхідна кількість SOL
            required_tokens: Словник необхідних токенів {адреса: кількість}
            commitment: Рівень підтвердження
            
        Returns:
            bool: True якщо балансів достатньо
            
        Raises:
            APIError: Помилка API
            ValueError: Некоректні параметри
        """
        if not address:
            raise ValueError("Необхідно вказати адресу гаманця")
            
        if required_sol < 0:
            raise ValueError("Кількість SOL не може бути від'ємною")
            
        commitment = commitment or self.default_commitment
        required_tokens = required_tokens or {}
        
        try:
            logger.info(
                f"Перевірка балансів для {address}: "
                f"SOL={required_sol}, tokens={required_tokens}"
            )
            
            # Перевіряємо SOL
            sol_balance = await self.get_sol_balance(address, commitment)
            if sol_balance < required_sol:
                logger.warning(
                    f"Недостатньо SOL: потрібно {required_sol}, "
                    f"наявно {sol_balance}"
                )
                return False
                
            # Перевіряємо токени
            for token_mint, required_amount in required_tokens.items():
                if required_amount < 0:
                    raise ValueError(
                        f"Кількість токена {token_mint} не може бути від'ємною"
                    )
                    
                token_balance = await self.get_token_balance(
                    address,
                    token_mint,
                    commitment
                )
                
                if token_balance < required_amount:
                    logger.warning(
                        f"Недостатньо {token_mint}: "
                        f"потрібно {required_amount}, наявно {token_balance}"
                    )
                    return False
                    
            logger.info("Перевірка балансів успішна")
            return True
            
        except APIError as e:
            logger.error(f"Помилка перевірки балансів для {address}: {str(e)}")
            raise
            
    async def _get_token_account(
        self,
        owner: str,
        token_mint: str,
        commitment: str
    ) -> Optional[str]:
        """
        Отримання адреси токен-акаунта
        
        Args:
            owner: Адреса власника
            token_mint: Адреса токена
            commitment: Рівень підтвердження
            
        Returns:
            Optional[str]: Адреса токен-акаунта або None
            
        Raises:
            APIError: Помилка API
        """
        try:
            # Отримуємо всі токен-акаунти
            response = await self._make_request(
                method="getTokenAccountsByOwner",
                params=[
                    owner,
                    {"programId": TOKEN_PROGRAM_ID},
                    {"encoding": "jsonParsed", "commitment": commitment}
                ]
            )
            
            # Шукаємо потрібний акаунт
            for account in response["value"]:
                if account["account"]["data"]["parsed"]["info"]["mint"] == token_mint:
                    return account["pubkey"]
                    
            return None
            
        except APIError as e:
            logger.error(
                f"Помилка отримання токен-акаунта {token_mint} "
                f"для {owner}: {str(e)}"
            )
            raise
