from typing import Dict, List, Optional
from utils import get_logger
from .base import BaseJupiterClient, APIError
from .constants import (
    API_ENDPOINTS,
    TOKEN_LIST_ENDPOINT,
    MAX_RETRIES,
    RETRY_DELAY,
    HEALTH_CHECK_INTERVAL,
    ErrorCode
)

logger = get_logger("jupiter_endpoint_manager")

class EndpointManager(BaseJupiterClient):
    """Менеджер ендпоінтів Jupiter API"""
    
    def __init__(
        self,
        ssl_context=None,
        max_retries: int = MAX_RETRIES,
        retry_delay: float = RETRY_DELAY
    ):
        """
        Ініціалізація менеджера ендпоінтів
        
        Args:
            ssl_context: SSL контекст для захищених з'єднань
            max_retries: Максимальна кількість повторних спроб
            retry_delay: Затримка між спробами в секундах
        """
        super().__init__(
            ssl_context=ssl_context,
            max_retries=max_retries,
            retry_delay=retry_delay
        )
        
        # Ендпоінти для різних версій API
        self.endpoints = API_ENDPOINTS
        
        # Ендпоінт для отримання списку токенів
        self.token_list_endpoint = TOKEN_LIST_ENDPOINT
        
        # Версії API в порядку пріоритету
        self.api_versions = list(API_ENDPOINTS.keys())
        
        # Кеш працюючих ендпоінтів
        self._working_endpoints = {}
        
        # Інтервал перевірки здоров'я
        self.health_check_interval = HEALTH_CHECK_INTERVAL
        
    async def get_endpoint(
        self,
        endpoint_type: str,
        preferred_version: Optional[str] = None
    ) -> str:
        """
        Отримання робочого ендпоінту заданого типу
        
        Args:
            endpoint_type: Тип ендпоінту ('quote', 'price', 'swap')
            preferred_version: Бажана версія API (опціонально)
            
        Returns:
            str: URL робочого ендпоінту
            
        Raises:
            APIError: Якщо не знайдено робочий ендпоінт
        """
        # Перевіряємо кеш
        cache_key = f"{endpoint_type}_{preferred_version or 'any'}"
        if cache_key in self._working_endpoints:
            return self._working_endpoints[cache_key]
            
        # Визначаємо порядок перевірки версій
        versions = (
            [preferred_version] if preferred_version
            else self.api_versions
        )
        
        # Перевіряємо ендпоінти
        for version in versions:
            if version not in self.endpoints:
                logger.warning(f"Версія API {version} не підтримується")
                continue
                
            if endpoint_type not in self.endpoints[version]:
                logger.warning(f"Тип ендпоінту {endpoint_type} не підтримується в версії {version}")
                continue
                
            url = self.endpoints[version][endpoint_type]
            
            try:
                # Перевіряємо доступність ендпоінту
                await self._make_request("GET", f"{url}/health-check")
                
                # Зберігаємо в кеш
                self._working_endpoints[cache_key] = url
                logger.info(f"Знайдено робочий ендпоінт {endpoint_type} в версії {version}: {url}")
                return url
                
            except Exception as e:
                logger.warning(
                    f"Ендпоінт {url} недоступний: {str(e)}"
                )
                continue
                
        error_msg = f"Не знайдено доступний ендпоінт типу {endpoint_type}"
        logger.error(error_msg)
        raise APIError(error_msg, code=ErrorCode.API_ERROR)
        
    async def clear_cache(self):
        """Очищення кешу робочих ендпоінтів"""
        self._working_endpoints.clear()
        logger.info("Кеш ендпоінтів очищено")
        
    def get_token_list_endpoint(self) -> str:
        """
        Отримання ендпоінту для списку токенів
        
        Returns:
            str: URL ендпоінту списку токенів
        """
        return self.token_list_endpoint
        
    async def health_check(self) -> Dict[str, Dict[str, bool]]:
        """
        Перевірка доступності всіх ендпоінтів
        
        Returns:
            Dict[str, Dict[str, bool]]: Статус кожного ендпоінту
        """
        results = {}
        
        for version in self.api_versions:
            results[version] = {}
            for endpoint_type, url in self.endpoints[version].items():
                try:
                    await self._make_request("GET", f"{url}/health-check")
                    results[version][endpoint_type] = True
                    logger.debug(f"Ендпоінт {url} доступний")
                except Exception as e:
                    results[version][endpoint_type] = False
                    logger.warning(f"Ендпоінт {url} недоступний: {str(e)}")
                    
        return results 