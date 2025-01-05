from typing import Dict, Optional, Any
import ssl
import json
import aiohttp
import asyncio
from datetime import datetime
from utils import get_logger
from utils.decorators import log_execution, measure_time
from .endpoint_manager import EndpointManager
from .constants import (
    ErrorCode,
    DEFAULT_MAX_RETRIES,
    DEFAULT_RETRY_DELAY,
    DEFAULT_TIMEOUT
)

logger = get_logger("quicknode_base_client")

class APIError(Exception):
    """Помилка API QuickNode"""
    def __init__(self, message: str, code: Optional[int] = None):
        super().__init__(message)
        self.code = code

class WebSocketError(Exception):
    """Помилка WebSocket з'єднання"""
    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(message)
        self.details = details

class BaseQuickNodeClient:
    """Базовий клас для роботи з QuickNode API"""
    
    def __init__(
        self,
        endpoint_manager: Optional[EndpointManager] = None,
        ssl_context: Optional[ssl.SSLContext] = None,
        max_retries: Optional[int] = None,
        retry_delay: Optional[int] = None
    ):
        """
        Ініціалізація базового клієнта
        
        Args:
            endpoint_manager: Менеджер ендпоінтів (опціонально)
            ssl_context: SSL контекст для захищених з'єднань
            max_retries: Максимальна кількість повторних спроб
            retry_delay: Затримка між спробами в секундах
        """
        self._endpoint_manager = endpoint_manager or EndpointManager()
        self._ssl_context = ssl_context or ssl.create_default_context()
        self._max_retries = max_retries or DEFAULT_MAX_RETRIES
        self._retry_delay = retry_delay or DEFAULT_RETRY_DELAY
        self._session = None
        logger.info(
            f"BaseQuickNodeClient ініціалізовано з max_retries={self._max_retries}, "
            f"retry_delay={self._retry_delay}"
        )
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """
        Отримання HTTP сесії
        
        Returns:
            aiohttp.ClientSession: HTTP сесія
        """
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=self._ssl_context)
            )
        return self._session
        
    async def _make_request(
        self,
        method: str,
        params: list,
        timeout: Optional[int] = None
    ) -> Any:
        """
        Виконання HTTP запиту до API
        
        Args:
            method: Метод API
            params: Параметри запиту
            timeout: Таймаут запиту в секундах
            
        Returns:
            Any: Результат запиту
            
        Raises:
            APIError: Помилка API
        """
        timeout = timeout or DEFAULT_TIMEOUT
        attempts = 0
        last_error = None
        
        while attempts < self._max_retries:
            try:
                # Отримуємо робочий ендпоінт
                endpoint = await self._endpoint_manager.get_endpoint()
                
                # Формуємо запит
                request_data = {
                    "jsonrpc": "2.0",
                    "id": str(int(datetime.now().timestamp() * 1000)),
                    "method": method,
                    "params": params
                }
                
                logger.debug(
                    f"Запит до {endpoint}: method={method}, params={params}"
                )
                
                # Виконуємо запит
                session = await self._get_session()
                async with session.post(
                    endpoint,
                    json=request_data,
                    timeout=timeout
                ) as response:
                    # Перевіряємо статус
                    if response.status != 200:
                        raise APIError(
                            f"HTTP помилка {response.status}",
                            ErrorCode.HTTP_ERROR
                        )
                        
                    # Парсимо відповідь
                    data = await response.json()
                    
                    # Перевіряємо помилки
                    if "error" in data:
                        error = data["error"]
                        raise APIError(
                            error.get("message", "Невідома помилка"),
                            error.get("code", ErrorCode.UNKNOWN_ERROR)
                        )
                        
                    # Повертаємо результат
                    return data.get("result")
                    
            except asyncio.TimeoutError:
                last_error = APIError(
                    f"Таймаут запиту ({timeout}с)",
                    ErrorCode.TIMEOUT
                )
                
            except aiohttp.ClientError as e:
                last_error = APIError(
                    f"Помилка HTTP клієнта: {str(e)}",
                    ErrorCode.CLIENT_ERROR
                )
                
            except APIError as e:
                # Якщо помилка API - пробуємо інший ендпоінт
                if e.code in [
                    ErrorCode.HTTP_ERROR,
                    ErrorCode.RATE_LIMIT,
                    ErrorCode.SERVER_ERROR
                ]:
                    await self._endpoint_manager.mark_failed(endpoint)
                else:
                    # Інші помилки API одразу повертаємо
                    raise
                    
                last_error = e
                
            except Exception as e:
                last_error = APIError(
                    f"Невідома помилка: {str(e)}",
                    ErrorCode.UNKNOWN_ERROR
                )
                
            # Збільшуємо лічильник спроб
            attempts += 1
            
            if attempts < self._max_retries:
                # Чекаємо перед повторною спробою
                await asyncio.sleep(self._retry_delay)
                logger.warning(
                    f"Повторна спроба {attempts}/{self._max_retries} "
                    f"через {self._retry_delay}с"
                )
                
        # Вичерпано всі спроби
        raise last_error or APIError(
            "Вичерпано всі спроби",
            ErrorCode.MAX_RETRIES
        )
        
    async def _create_ws_connection(self, url: str) -> aiohttp.ClientWebSocketResponse:
        """
        Створення WebSocket з'єднання
        
        Args:
            url: WebSocket URL
            
        Returns:
            aiohttp.ClientWebSocketResponse: WebSocket з'єднання
            
        Raises:
            WebSocketError: Помилка підключення
        """
        try:
            session = await self._get_session()
            ws = await session.ws_connect(
                url,
                ssl=self._ssl_context,
                heartbeat=30
            )
            return ws
            
        except Exception as e:
            raise WebSocketError("Помилка WebSocket підключення", str(e))
            
    async def close(self):
        """Закриття з'єднань"""
        if self._session and not self._session.closed:
            await self._session.close() 