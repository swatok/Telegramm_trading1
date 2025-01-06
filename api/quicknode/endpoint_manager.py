from typing import Dict, Optional, List
import asyncio
import random
from datetime import datetime, timedelta
from utils import get_logger
from utils.decorators import log_execution, measure_time
from .constants import (
    ErrorCode,
    DEFAULT_HEALTH_CHECK_INTERVAL,
    DEFAULT_ENDPOINT_TIMEOUT,
    DEFAULT_ENDPOINTS
)

logger = get_logger("quicknode_endpoint_manager")

class EndpointManager:
    """Менеджер ендпоінтів QuickNode"""
    
    def __init__(
        self,
        endpoints: Optional[List[str]] = None,
        health_check_interval: int = DEFAULT_HEALTH_CHECK_INTERVAL,
        endpoint_timeout: int = DEFAULT_ENDPOINT_TIMEOUT
    ):
        """
        Ініціалізація менеджера ендпоінтів
        
        Args:
            endpoints: Список ендпоінтів (опціонально)
            health_check_interval: Інтервал перевірки здоров'я в секундах
            endpoint_timeout: Таймаут ендпоінта в секундах
        """
        self._endpoints = endpoints or DEFAULT_ENDPOINTS.copy()
        self._health_check_interval = health_check_interval
        self._endpoint_timeout = endpoint_timeout
        self._endpoint_status = {}
        self._last_health_check = None
        self._health_check_lock = asyncio.Lock()
        logger.info(
            f"EndpointManager ініціалізовано з {len(self._endpoints)} ендпоінтами, "
            f"health_check_interval={health_check_interval}, "
            f"endpoint_timeout={endpoint_timeout}"
        )
        
    @log_execution
    async def get_endpoint(self) -> str:
        """
        Отримання робочого ендпоінта
        
        Returns:
            str: URL ендпоінта
            
        Raises:
            RuntimeError: Немає доступних ендпоінтів
        """
        # Перевіряємо здоров'я якщо потрібно
        await self._check_health_if_needed()
        
        # Фільтруємо робочі ендпоінти
        working_endpoints = [
            endpoint for endpoint in self._endpoints
            if self._is_endpoint_working(endpoint)
        ]
        
        if not working_endpoints:
            logger.error("Немає доступних ендпоінтів")
            raise RuntimeError("Немає доступних ендпоінтів")
            
        # Вибираємо випадковий ендпоінт
        endpoint = random.choice(working_endpoints)
        logger.debug(f"Вибрано ендпоінт {endpoint}")
        
        return endpoint
        
    @log_execution
    async def get_ws_endpoint(self) -> str:
        """
        Отримання WebSocket ендпоінта
        
        Returns:
            str: WebSocket URL
            
        Raises:
            RuntimeError: Немає доступних ендпоінтів
        """
        # Отримуємо HTTP ендпоінт
        endpoint = await self.get_endpoint()
        
        # Конвертуємо в WebSocket URL
        ws_endpoint = endpoint.replace("http", "ws")
        logger.debug(f"WebSocket ендпоінт: {ws_endpoint}")
        
        return ws_endpoint
        
    @log_execution
    async def mark_failed(self, endpoint: str):
        """
        Позначення ендпоінта як непрацюючого
        
        Args:
            endpoint: URL ендпоінта
        """
        if endpoint not in self._endpoints:
            return
            
        logger.warning(f"Позначаємо ендпоінт {endpoint} як непрацюючий")
        self._endpoint_status[endpoint] = {
            "working": False,
            "last_check": datetime.now(),
            "error_count": self._endpoint_status.get(endpoint, {}).get("error_count", 0) + 1
        }
        
    async def _check_health_if_needed(self):
        """Перевірка здоров'я ендпоінтів якщо потрібно"""
        now = datetime.now()
        
        # Перевіряємо чи потрібна перевірка
        if (
            self._last_health_check and
            now - self._last_health_check < timedelta(seconds=self._health_check_interval)
        ):
            return
            
        # Блокуємо щоб уникнути паралельних перевірок
        async with self._health_check_lock:
            # Повторно перевіряємо після блокування
            if (
                self._last_health_check and
                now - self._last_health_check < timedelta(seconds=self._health_check_interval)
            ):
                return
                
            await self._check_health()
            
    @log_execution
    async def _check_health(self):
        """Перевірка здоров'я всіх ендпоінтів"""
        logger.info("Запуск перевірки здоров'я ендпоінтів")
        
        # Перевіряємо кожен ендпоінт
        for endpoint in self._endpoints:
            try:
                # Виконуємо тестовий запит
                async with asyncio.timeout(self._endpoint_timeout):
                    # TODO: Реалізувати тестовий запит
                    is_working = True
                    
                self._endpoint_status[endpoint] = {
                    "working": is_working,
                    "last_check": datetime.now(),
                    "error_count": 0 if is_working else self._endpoint_status.get(endpoint, {}).get("error_count", 0)
                }
                
                logger.info(f"Ендпоінт {endpoint} {'працює' if is_working else 'не працює'}")
                
            except Exception as e:
                logger.error(f"Помилка перевірки ендпоінта {endpoint}: {str(e)}")
                self._endpoint_status[endpoint] = {
                    "working": False,
                    "last_check": datetime.now(),
                    "error_count": self._endpoint_status.get(endpoint, {}).get("error_count", 0) + 1
                }
                
        self._last_health_check = datetime.now()
        
    def _is_endpoint_working(self, endpoint: str) -> bool:
        """
        Перевірка чи працює ендпоінт
        
        Args:
            endpoint: URL ендпоінта
            
        Returns:
            bool: True якщо ендпоінт працює
        """
        status = self._endpoint_status.get(endpoint)
        
        if not status:
            # Якщо статус невідомий - вважаємо що працює
            return True
            
        if not status["working"]:
            # Якщо помічений як непрацюючий
            return False
            
        # Перевіряємо час останньої перевірки
        if datetime.now() - status["last_check"] > timedelta(seconds=self._endpoint_timeout):
            # Якщо давно не перевіряли - вважаємо що не працює
            return False
            
        return True 