from typing import Dict, Optional, List, Callable, Any
import asyncio
from datetime import datetime, timedelta
from utils import get_logger
from utils.decorators import log_execution, measure_time
from .base import BaseQuickNodeClient, APIError
from .websocket_manager import WebSocketManager
from .constants import (
    ErrorCode,
    DEFAULT_COMMITMENT,
    DEFAULT_TIMEOUT,
    DEFAULT_CONFIRMATION_TIMEOUT,
    TransactionStatus
)

logger = get_logger("quicknode_transaction_monitor")

class TransactionMonitor(BaseQuickNodeClient):
    """Моніторинг транзакцій через QuickNode"""
    
    def __init__(
        self,
        endpoint_manager=None,
        ssl_context=None,
        max_retries=None,
        retry_delay=None,
        default_commitment: str = DEFAULT_COMMITMENT,
        default_timeout: int = DEFAULT_TIMEOUT,
        confirmation_timeout: int = DEFAULT_CONFIRMATION_TIMEOUT
    ):
        """
        Ініціалізація моніторингу транзакцій
        
        Args:
            endpoint_manager: Менеджер ендпоінтів (опціонально)
            ssl_context: SSL контекст для захищених з'єднань
            max_retries: Максимальна кількість повторних спроб
            retry_delay: Затримка між спробами в секундах
            default_commitment: Рівень підтвердження за замовчуванням
            default_timeout: Таймаут за замовчуванням
            confirmation_timeout: Таймаут очікування підтвердження
        """
        super().__init__(
            endpoint_manager=endpoint_manager,
            ssl_context=ssl_context,
            max_retries=max_retries,
            retry_delay=retry_delay
        )
        self.default_commitment = default_commitment
        self.default_timeout = default_timeout
        self.confirmation_timeout = confirmation_timeout
        self._ws_manager = WebSocketManager(
            endpoint_manager=endpoint_manager,
            ssl_context=ssl_context,
            max_retries=max_retries,
            retry_delay=retry_delay,
            default_commitment=default_commitment,
            default_timeout=default_timeout
        )
        logger.info(
            f"TransactionMonitor ініціалізовано з commitment={default_commitment}, "
            f"timeout={default_timeout}, confirmation_timeout={confirmation_timeout}"
        )
        
    @log_execution
    @measure_time
    async def get_transaction_status(
        self,
        signature: str,
        commitment: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Отримання статусу транзакції
        
        Args:
            signature: Підпис транзакції
            commitment: Рівень підтвердження
            
        Returns:
            Optional[Dict]: Статус транзакції або None
            
        Raises:
            APIError: Помилка при отриманні статусу
            ValueError: Некоректні параметри
        """
        if not signature:
            raise ValueError("Необхідно вказати підпис транзакції")
            
        commitment = commitment or self.default_commitment
        
        try:
            logger.info(f"Запит статусу транзакції {signature}")
            
            # Виконуємо запит
            response = await self._make_request(
                method="getTransaction",
                params=[
                    signature,
                    {"commitment": commitment, "encoding": "jsonParsed"}
                ]
            )
            
            if not response:
                logger.warning(f"Транзакцію {signature} не знайдено")
                return None
                
            # Визначаємо статус
            if "err" in response:
                status = TransactionStatus.FAILED
            else:
                confirmations = response.get("confirmations", 0)
                if confirmations >= 32:
                    status = TransactionStatus.FINALIZED
                elif confirmations > 0:
                    status = TransactionStatus.CONFIRMED
                else:
                    status = TransactionStatus.PENDING
                    
            result = {
                "status": status,
                "confirmations": response.get("confirmations", 0),
                "error": response.get("err"),
                "slot": response.get("slot"),
                "blockTime": response.get("blockTime")
            }
            
            logger.info(f"Отримано статус транзакції {signature}: {status}")
            return result
            
        except APIError as e:
            logger.error(f"Помилка отримання статусу транзакції {signature}: {str(e)}")
            raise
            
    @log_execution
    async def wait_for_confirmation(
        self,
        signature: str,
        commitment: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> Optional[Dict]:
        """
        Очікування підтвердження транзакції
        
        Args:
            signature: Підпис транзакції
            commitment: Рівень підтвердження
            timeout: Таймаут очікування в секундах
            
        Returns:
            Optional[Dict]: Статус транзакції або None
            
        Raises:
            APIError: Помилка при очікуванні
            ValueError: Некоректні параметри
            TimeoutError: Перевищено час очікування
        """
        if not signature:
            raise ValueError("Необхідно вказати підпис транзакції")
            
        commitment = commitment or self.default_commitment
        timeout = timeout or self.confirmation_timeout
        deadline = datetime.now() + timedelta(seconds=timeout)
        
        try:
            logger.info(
                f"Очікування підтвердження транзакції {signature} "
                f"(таймаут: {timeout}с)"
            )
            
            while datetime.now() < deadline:
                # Отримуємо поточний статус
                status = await self.get_transaction_status(signature, commitment)
                
                if not status:
                    # Транзакція ще не потрапила в блокчейн
                    await asyncio.sleep(1)
                    continue
                    
                if status["status"] == TransactionStatus.FAILED:
                    # Транзакція завершилась з помилкою
                    logger.error(
                        f"Транзакція {signature} завершилась з помилкою: "
                        f"{status['error']}"
                    )
                    return status
                    
                if status["status"] == TransactionStatus.FINALIZED:
                    # Транзакція підтверджена
                    logger.info(f"Транзакція {signature} підтверджена")
                    return status
                    
                # Очікуємо далі
                await asyncio.sleep(1)
                
            # Перевищено час очікування
            logger.error(
                f"Перевищено час очікування підтвердження транзакції {signature}"
            )
            raise TimeoutError("Перевищено час очікування підтвердження")
            
        except APIError as e:
            logger.error(f"Помилка очікування підтвердження {signature}: {str(e)}")
            raise
            
    @log_execution
    async def subscribe_transaction(
        self,
        signature: str,
        callback: Callable[[Dict], Any],
        commitment: Optional[str] = None
    ):
        """
        Підписка на оновлення статусу транзакції
        
        Args:
            signature: Підпис транзакції
            callback: Функція для обробки оновлень
            commitment: Рівень підтвердження
            
        Raises:
            APIError: Помилка підписки
            ValueError: Некоректні параметри
        """
        if not signature:
            raise ValueError("Необхідно вказати підпис транзакції")
            
        if not callback:
            raise ValueError("Необхідно вказати callback")
            
        commitment = commitment or self.default_commitment
        
        try:
            logger.info(f"Підписка на оновлення транзакції {signature}")
            
            # Підключаємо WebSocket якщо потрібно
            if not self._ws_manager._ws:
                await self._ws_manager.connect()
                
            # Підписуємось на оновлення
            await self._ws_manager.subscribe_signature(
                signature,
                callback,
                commitment
            )
            
            logger.info(f"Підписку на транзакцію {signature} встановлено")
            
        except Exception as e:
            logger.error(f"Помилка підписки на транзакцію {signature}: {str(e)}")
            raise
            
    @log_execution
    async def monitor_transactions(
        self,
        signatures: List[str],
        callback: Callable[[Dict], Any],
        commitment: Optional[str] = None
    ):
        """
        Моніторинг списку транзакцій
        
        Args:
            signatures: Список підписів транзакцій
            callback: Функція для обробки оновлень
            commitment: Рівень підтвердження
            
        Raises:
            APIError: Помилка моніторингу
            ValueError: Некоректні параметри
        """
        if not signatures:
            raise ValueError("Необхідно вказати список транзакцій")
            
        if not callback:
            raise ValueError("Необхідно вказати callback")
            
        commitment = commitment or self.default_commitment
        
        try:
            logger.info(f"Запуск моніторингу {len(signatures)} транзакцій")
            
            # Підключаємо WebSocket якщо потрібно
            if not self._ws_manager._ws:
                await self._ws_manager.connect()
                
            # Підписуємось на всі транзакції
            for signature in signatures:
                await self._ws_manager.subscribe_signature(
                    signature,
                    callback,
                    commitment
                )
                
            logger.info(f"Моніторинг {len(signatures)} транзакцій запущено")
            
        except Exception as e:
            logger.error(f"Помилка запуску моніторингу транзакцій: {str(e)}")
            raise
            
    async def close(self):
        """Закриття з'єднань"""
        await self._ws_manager.disconnect()
