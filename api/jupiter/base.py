import ssl
import aiohttp
import asyncio
from typing import Optional, Dict, Any
from utils import get_logger
from utils.decorators import log_execution, measure_time
from .constants import (
    MAX_RETRIES,
    RETRY_DELAY,
    HEALTH_CHECK_INTERVAL,
    DEFAULT_TIMEOUT,
    ErrorCode,
    REQUEST_HEADERS
)

logger = get_logger("jupiter_base")

class BaseJupiterClient:
    """Базовий клас для роботи з Jupiter API"""
    
    def __init__(
        self,
        endpoint_manager=None,
        ssl_context: Optional[ssl.SSLContext] = None,
        max_retries: int = MAX_RETRIES,
        retry_delay: float = RETRY_DELAY,
        timeout: float = DEFAULT_TIMEOUT
    ):
        """
        Ініціалізація базового клієнта
        
        Args:
            endpoint_manager: Менеджер ендпоінтів (опціонально)
            ssl_context: SSL контекст для захищених з'єднань
            max_retries: Максимальна кількість повторних спроб
            retry_delay: Затримка між спробами в секундах
            timeout: Таймаут для запитів в секундах
        """
        logger.info("Ініціалізація BaseJupiterClient")
        
        # Створюємо SSL контекст якщо не переданий
        self.ssl_context = ssl_context or self._create_ssl_context()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.session = None
        
        # Зберігаємо або створюємо endpoint_manager
        if endpoint_manager:
            logger.info("Використовуємо переданий EndpointManager")
            self.endpoint_manager = endpoint_manager
        else:
            logger.info("Створюємо новий EndpointManager")
            from .endpoint_manager import EndpointManager
            self.endpoint_manager = EndpointManager(
                ssl_context=self.ssl_context,
                max_retries=self.max_retries,
                retry_delay=self.retry_delay
            )
            
        # Запускаємо періодичну перевірку здоров'я
        self._start_health_check()
        logger.info("BaseJupiterClient успішно ініціалізовано")
        
    def _create_ssl_context(self) -> ssl.SSLContext:
        """Створення SSL контексту з базовими налаштуваннями"""
        logger.debug("Створення SSL контексту")
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context
        
    @measure_time
    async def _get_session(self) -> aiohttp.ClientSession:
        """Отримання або створення HTTP сесії"""
        if not self.session or self.session.closed:
            logger.debug("Створення нової HTTP сесії")
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=self.ssl_context),
                timeout=timeout,
                headers=REQUEST_HEADERS
            )
        return self.session
        
    def _start_health_check(self):
        """Запуск періодичної перевірки здоров'я ендпоінтів"""
        logger.info(f"Запуск перевірки здоров'я з інтервалом {HEALTH_CHECK_INTERVAL} секунд")
        
        async def health_check_loop():
            while True:
                try:
                    logger.debug("Виконання перевірки здоров'я ендпоінтів")
                    results = await self.endpoint_manager.health_check()
                    
                    # Логуємо результати перевірки
                    for version, endpoints in results.items():
                        for endpoint_type, is_healthy in endpoints.items():
                            status = "доступний" if is_healthy else "недоступний"
                            logger.info(f"Ендпоінт {endpoint_type} (v{version}): {status}")
                            
                except Exception as e:
                    logger.error(f"Помилка перевірки здоров'я: {str(e)}", exc_info=True)
                    
                await asyncio.sleep(HEALTH_CHECK_INTERVAL)
                
        asyncio.create_task(health_check_loop())
        
    async def close(self):
        """Закриття з'єднань"""
        logger.info("Закриття з'єднань BaseJupiterClient")
        if self.session and not self.session.closed:
            logger.debug("Закриття HTTP сесії")
            await self.session.close()
        logger.debug("Закриття EndpointManager")
        await self.endpoint_manager.close()
            
    async def __aenter__(self):
        """Контекстний менеджер - вхід"""
        logger.debug("Вхід в контекстний менеджер")
        await self._get_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Контекстний менеджер - вихід"""
        logger.debug("Вихід з контекстного менеджера")
        await self.close()
        
    @log_execution
    @measure_time
    async def _make_request(
        self,
        method: str,
        endpoint_type: str,
        path: str = "",
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        preferred_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Виконання HTTP запиту з повторними спробами
        
        Args:
            method: HTTP метод ('GET', 'POST', etc.)
            endpoint_type: Тип ендпоінту ('quote', 'price', 'swap')
            path: Додатковий шлях до ендпоінту
            params: Параметри URL (опціонально)
            json: JSON дані для тіла запиту (опціонально)
            headers: HTTP заголовки (опціонально)
            preferred_version: Бажана версія API (опціонально)
            
        Returns:
            Dict[str, Any]: Відповідь від API
            
        Raises:
            APIError: Помилка при виконанні запиту
            NetworkError: Помилка мережі
            TimeoutError: Перевищено час очікування
        """
        session = await self._get_session()
        
        # Логуємо параметри запиту
        logger.info(
            f"Виконання {method} запиту до {endpoint_type}"
            f"{f' (v{preferred_version})' if preferred_version else ''}"
        )
        logger.debug(f"Параметри запиту: path={path}, params={params}, json={json}")
        
        for attempt in range(self.max_retries):
            try:
                # Отримуємо актуальний ендпоінт
                base_url = await self.endpoint_manager.get_endpoint(
                    endpoint_type,
                    preferred_version
                )
                
                # Формуємо повний URL
                url = f"{base_url}/{path.lstrip('/')}" if path else base_url
                
                logger.debug(
                    f"Спроба {attempt + 1}/{self.max_retries}: "
                    f"{method} {url}"
                )
                
                request_start = asyncio.get_event_loop().time()
                async with session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json,
                    headers=headers,
                    ssl=self.ssl_context
                ) as response:
                    request_time = asyncio.get_event_loop().time() - request_start
                    logger.debug(f"Час виконання запиту: {request_time:.3f} секунд")
                    
                    if response.status == 200:
                        data = await response.json()
                        logger.debug(f"Отримано успішну відповідь: {data}")
                        return data
                        
                    # Якщо помилка 5xx - повторюємо
                    if 500 <= response.status < 600 and attempt < self.max_retries - 1:
                        error_text = await response.text()
                        logger.warning(
                            f"Отримано помилку сервера {response.status}: {error_text}. "
                            f"Повторна спроба через {self.retry_delay * (attempt + 1)} секунд"
                        )
                        await asyncio.sleep(self.retry_delay * (attempt + 1))
                        continue
                        
                    error_text = await response.text()
                    error_msg = (
                        f"API повернув помилку {response.status}: {error_text}. "
                        f"URL: {url}, Метод: {method}"
                    )
                    logger.error(error_msg)
                    raise APIError(error_msg, code=ErrorCode.API_ERROR)
                    
            except aiohttp.ClientError as e:
                logger.warning(
                    f"Помилка мережі при спробі {attempt + 1}: {str(e)}. "
                    f"URL: {url}, Метод: {method}",
                    exc_info=True
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                raise NetworkError(f"Помилка мережі: {str(e)}")
                
            except asyncio.TimeoutError:
                logger.warning(
                    f"Таймаут при спробі {attempt + 1}. "
                    f"URL: {url}, Метод: {method}, Таймаут: {self.timeout} секунд"
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                raise TimeoutError(
                    f"Перевищено час очікування запиту ({self.timeout} секунд)"
                )
                
            except Exception as e:
                logger.error(
                    f"Неочікувана помилка: {str(e)}. "
                    f"URL: {url}, Метод: {method}",
                    exc_info=True
                )
                raise
                
        error_msg = (
            f"Вичерпано {self.max_retries} спроб запиту. "
            f"URL: {url}, Метод: {method}"
        )
        logger.error(error_msg)
        raise MaxRetriesError(error_msg)


class APIError(Exception):
    """Помилка відповіді API"""
    def __init__(self, message: str, code: str = ErrorCode.API_ERROR):
        super().__init__(message)
        self.code = code
        logger.error(f"APIError: {message} (код: {code})")

class NetworkError(Exception):
    """Помилка мережі"""
    def __init__(self, message: str):
        super().__init__(message)
        self.code = ErrorCode.NETWORK_ERROR
        logger.error(f"NetworkError: {message}")

class TimeoutError(Exception):
    """Перевищено час очікування"""
    def __init__(self, message: str):
        super().__init__(message)
        self.code = ErrorCode.NETWORK_ERROR
        logger.error(f"TimeoutError: {message}")

class MaxRetriesError(Exception):
    """Вичерпано максимальну кількість спроб"""
    def __init__(self, message: str):
        super().__init__(message)
        self.code = ErrorCode.NETWORK_ERROR
        logger.error(f"MaxRetriesError: {message}") 