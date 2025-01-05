from typing import Dict, Optional, Any, Callable
import asyncio
import json
from datetime import datetime
from utils import get_logger
from utils.decorators import log_execution, measure_time
from .base import BaseQuickNodeClient, WebSocketError
from .constants import (
    ErrorCode,
    DEFAULT_COMMITMENT,
    DEFAULT_TIMEOUT,
    DEFAULT_RECONNECT_DELAY,
    MAX_RECONNECT_ATTEMPTS
)

logger = get_logger("quicknode_websocket_manager")

class WebSocketManager(BaseQuickNodeClient):
    """Менеджер WebSocket з'єднань QuickNode"""
    
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
        Ініціалізація WebSocket менеджера
        
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
        self._ws = None
        self._subscriptions = {}
        self._message_handlers = {}
        self._reconnect_task = None
        self._receive_task = None
        logger.info(
            f"WebSocketManager ініціалізовано з commitment={default_commitment}, "
            f"timeout={default_timeout}"
        )
        
    @log_execution
    async def connect(self):
        """
        Підключення до WebSocket
        
        Raises:
            WebSocketError: Помилка підключення
        """
        if self._ws:
            return
            
        try:
            # Отримуємо WebSocket URL
            ws_url = await self._endpoint_manager.get_ws_endpoint()
            
            # Створюємо з'єднання
            self._ws = await self._create_ws_connection(ws_url)
            logger.info(f"WebSocket підключено до {ws_url}")
            
            # Запускаємо обробку повідомлень
            self._receive_task = asyncio.create_task(self._receive_messages())
            
        except Exception as e:
            logger.error(f"Помилка WebSocket підключення: {str(e)}")
            raise WebSocketError("Помилка WebSocket підключення", str(e))
            
    @log_execution
    async def disconnect(self):
        """Відключення від WebSocket"""
        if not self._ws:
            return
            
        try:
            # Зупиняємо задачі
            if self._receive_task:
                self._receive_task.cancel()
                self._receive_task = None
                
            if self._reconnect_task:
                self._reconnect_task.cancel()
                self._reconnect_task = None
                
            # Закриваємо з'єднання
            await self._ws.close()
            self._ws = None
            
            # Очищаємо підписки
            self._subscriptions.clear()
            self._message_handlers.clear()
            
            logger.info("WebSocket відключено")
            
        except Exception as e:
            logger.error(f"Помилка закриття WebSocket: {str(e)}")
            
    @log_execution
    async def subscribe_signature(
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
            WebSocketError: Помилка підписки
            ValueError: Некоректні параметри
        """
        if not signature:
            raise ValueError("Необхідно вказати підпис транзакції")
            
        if not callback:
            raise ValueError("Необхідно вказати callback")
            
        commitment = commitment or self.default_commitment
        
        try:
            # Підключаємо WebSocket якщо потрібно
            if not self._ws:
                await self.connect()
                
            # Формуємо запит підписки
            subscription_id = str(int(datetime.now().timestamp() * 1000))
            request = {
                "jsonrpc": "2.0",
                "id": subscription_id,
                "method": "signatureSubscribe",
                "params": [
                    signature,
                    {"commitment": commitment}
                ]
            }
            
            # Зберігаємо callback
            self._message_handlers[subscription_id] = callback
            
            # Відправляємо запит
            await self._ws.send_json(request)
            logger.info(f"Відправлено запит підписки на {signature}")
            
            # Чекаємо підтвердження
            response = await self._wait_response(subscription_id)
            
            if "error" in response:
                error = response["error"]
                raise WebSocketError(
                    error.get("message", "Невідома помилка"),
                    error.get("code", ErrorCode.UNKNOWN_ERROR)
                )
                
            # Зберігаємо підписку
            subscription = response["result"]
            self._subscriptions[subscription] = {
                "signature": signature,
                "callback": callback,
                "commitment": commitment
            }
            
            logger.info(f"Підписку на {signature} встановлено")
            
        except Exception as e:
            logger.error(f"Помилка підписки на {signature}: {str(e)}")
            raise
            
    async def _receive_messages(self):
        """Обробка вхідних повідомлень"""
        try:
            while True:
                # Отримуємо повідомлення
                message = await self._ws.receive_json()
                
                try:
                    # Перевіряємо тип повідомлення
                    if "method" in message:
                        # Це оновлення підписки
                        await self._handle_subscription_update(message)
                    else:
                        # Це відповідь на запит
                        await self._handle_response(message)
                        
                except Exception as e:
                    logger.error(f"Помилка обробки повідомлення: {str(e)}")
                    
        except asyncio.CancelledError:
            # Нормальне завершення
            pass
            
        except Exception as e:
            logger.error(f"Помилка отримання повідомлень: {str(e)}")
            # Запускаємо перепідключення
            self._start_reconnect()
            
    async def _handle_subscription_update(self, message: Dict):
        """
        Обробка оновлення підписки
        
        Args:
            message: Повідомлення
        """
        try:
            # Отримуємо дані підписки
            subscription = message["params"]["subscription"]
            if subscription not in self._subscriptions:
                logger.warning(f"Отримано оновлення для невідомої підписки {subscription}")
                return
                
            # Викликаємо callback
            subscription_data = self._subscriptions[subscription]
            await subscription_data["callback"](message["params"]["result"])
            
        except Exception as e:
            logger.error(f"Помилка обробки оновлення підписки: {str(e)}")
            
    async def _handle_response(self, message: Dict):
        """
        Обробка відповіді на запит
        
        Args:
            message: Повідомлення
        """
        try:
            # Отримуємо ID запиту
            request_id = message["id"]
            if request_id not in self._message_handlers:
                logger.warning(f"Отримано відповідь для невідомого запиту {request_id}")
                return
                
            # Викликаємо callback
            await self._message_handlers[request_id](message)
            
            # Видаляємо callback
            del self._message_handlers[request_id]
            
        except Exception as e:
            logger.error(f"Помилка обробки відповіді: {str(e)}")
            
    async def _wait_response(self, request_id: str) -> Dict:
        """
        Очікування відповіді на запит
        
        Args:
            request_id: ID запиту
            
        Returns:
            Dict: Відповідь
            
        Raises:
            TimeoutError: Перевищено час очікування
        """
        future = asyncio.Future()
        self._message_handlers[request_id] = future.set_result
        
        try:
            return await asyncio.wait_for(future, self.default_timeout)
        finally:
            self._message_handlers.pop(request_id, None)
            
    def _start_reconnect(self):
        """Запуск перепідключення"""
        if not self._reconnect_task:
            self._reconnect_task = asyncio.create_task(self._reconnect())
            
    async def _reconnect(self):
        """Процес перепідключення"""
        attempts = 0
        
        while attempts < MAX_RECONNECT_ATTEMPTS:
            try:
                logger.info(f"Спроба перепідключення {attempts + 1}/{MAX_RECONNECT_ATTEMPTS}")
                
                # Закриваємо старе з'єднання
                if self._ws:
                    await self._ws.close()
                    self._ws = None
                    
                # Підключаємось
                await self.connect()
                
                # Відновлюємо підписки
                for subscription_id, subscription in self._subscriptions.items():
                    await self.subscribe_signature(
                        subscription["signature"],
                        subscription["callback"],
                        subscription["commitment"]
                    )
                    
                logger.info("Перепідключення успішне")
                return
                
            except Exception as e:
                logger.error(f"Помилка перепідключення: {str(e)}")
                attempts += 1
                
                if attempts < MAX_RECONNECT_ATTEMPTS:
                    await asyncio.sleep(DEFAULT_RECONNECT_DELAY)
                    
        logger.error("Вичерпано всі спроби перепідключення")
        # TODO: Сповістити про помилку
