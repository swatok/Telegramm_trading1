"""
Модуль для управління WebSocket підключеннями.
Відповідає за встановлення та підтримку WebSocket з'єднань.
"""

import asyncio
from typing import Dict, Set, Optional, Callable, Any
import json
import websockets
from websockets.exceptions import ConnectionClosed

from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class WebSocketManager:
    """
    Клас для управління WebSocket підключеннями.
    Забезпечує підключення та обробку WebSocket повідомлень.
    """

    def __init__(self):
        """Ініціалізація менеджера WebSocket."""
        self._connections: Dict[str, websockets.WebSocketClientProtocol] = {}
        self._subscriptions: Dict[str, Set[str]] = {}
        self._message_handlers: Dict[str, Callable] = {}
        self._reconnect_attempts: Dict[str, int] = {}
        self._active = False

    async def connect(self, url: str, connection_id: str):
        """
        Встановлення WebSocket з'єднання.

        Args:
            url: URL для підключення
            connection_id: Ідентифікатор з'єднання
        """
        try:
            connection = await websockets.connect(url)
            self._connections[connection_id] = connection
            self._subscriptions[connection_id] = set()
            self._reconnect_attempts[connection_id] = 0
            logger.info(f"WebSocket з'єднання встановлено: {connection_id}")
            return True
        except Exception as e:
            logger.error(f"Помилка підключення WebSocket {connection_id}: {e}")
            return False

    async def disconnect(self, connection_id: str):
        """
        Закриття WebSocket з'єднання.

        Args:
            connection_id: Ідентифікатор з'єднання
        """
        if connection_id in self._connections:
            try:
                await self._connections[connection_id].close()
                self._cleanup_connection(connection_id)
                logger.info(f"WebSocket з'єднання закрито: {connection_id}")
            except Exception as e:
                logger.error(f"Помилка закриття WebSocket {connection_id}: {e}")

    def _cleanup_connection(self, connection_id: str):
        """
        Очищення даних з'єднання.

        Args:
            connection_id: Ідентифікатор з'єднання
        """
        self._connections.pop(connection_id, None)
        self._subscriptions.pop(connection_id, None)
        self._reconnect_attempts.pop(connection_id, None)

    async def subscribe(self, connection_id: str, channel: str, handler: Callable):
        """
        Підписка на канал WebSocket.

        Args:
            connection_id: Ідентифікатор з'єднання
            channel: Канал для підписки
            handler: Обробник повідомлень
        """
        if connection_id not in self._connections:
            logger.error(f"З'єднання не знайдено: {connection_id}")
            return False

        try:
            subscription_message = {
                "type": "subscribe",
                "channel": channel
            }
            await self._connections[connection_id].send(json.dumps(subscription_message))
            self._subscriptions[connection_id].add(channel)
            self._message_handlers[f"{connection_id}:{channel}"] = handler
            logger.info(f"Підписка на канал {channel} встановлена")
            return True
        except Exception as e:
            logger.error(f"Помилка підписки на канал {channel}: {e}")
            return False

    async def unsubscribe(self, connection_id: str, channel: str):
        """
        Відписка від каналу WebSocket.

        Args:
            connection_id: Ідентифікатор з'єднання
            channel: Канал для відписки
        """
        if connection_id not in self._connections:
            return

        try:
            unsubscription_message = {
                "type": "unsubscribe",
                "channel": channel
            }
            await self._connections[connection_id].send(json.dumps(unsubscription_message))
            self._subscriptions[connection_id].discard(channel)
            self._message_handlers.pop(f"{connection_id}:{channel}", None)
            logger.info(f"Відписка від каналу {channel}")
        except Exception as e:
            logger.error(f"Помилка відписки від каналу {channel}: {e}")

    async def start_listening(self):
        """Запуск прослуховування всіх з'єднань."""
        self._active = True
        tasks = [
            self._listen_connection(conn_id, connection)
            for conn_id, connection in self._connections.items()
        ]
        await asyncio.gather(*tasks)

    async def stop_listening(self):
        """Зупинка прослуховування всіх з'єднань."""
        self._active = False
        for connection_id in list(self._connections.keys()):
            await self.disconnect(connection_id)

    async def _listen_connection(self, connection_id: str, connection: websockets.WebSocketClientProtocol):
        """
        Прослуховування конкретного з'єднання.

        Args:
            connection_id: Ідентифікатор з'єднання
            connection: Об'єкт WebSocket з'єднання
        """
        while self._active:
            try:
                message = await connection.recv()
                await self._handle_message(connection_id, message)
                self._reconnect_attempts[connection_id] = 0
            except ConnectionClosed:
                logger.warning(f"З'єднання втрачено: {connection_id}")
                await self._handle_reconnection(connection_id)
            except Exception as e:
                logger.error(f"Помилка обробки повідомлення {connection_id}: {e}")
                await asyncio.sleep(1)

    async def _handle_message(self, connection_id: str, message: str):
        """
        Обробка отриманого повідомлення.

        Args:
            connection_id: Ідентифікатор з'єднання
            message: Отримане повідомлення
        """
        try:
            data = json.loads(message)
            channel = data.get('channel')
            if channel:
                handler = self._message_handlers.get(f"{connection_id}:{channel}")
                if handler:
                    await handler(data)
        except json.JSONDecodeError:
            logger.error(f"Неправильний формат повідомлення: {message}")
        except Exception as e:
            logger.error(f"Помилка обробки повідомлення: {e}")

    async def _handle_reconnection(self, connection_id: str):
        """
        Обробка перепідключення.

        Args:
            connection_id: Ідентифікатор з'єднання
        """
        if not self._active:
            return

        self._reconnect_attempts[connection_id] = self._reconnect_attempts.get(connection_id, 0) + 1
        if self._reconnect_attempts[connection_id] > 5:
            logger.error(f"Досягнуто максимальну кількість спроб перепідключення: {connection_id}")
            self._cleanup_connection(connection_id)
            return

        delay = min(2 ** self._reconnect_attempts[connection_id], 30)
        logger.info(f"Спроба перепідключення через {delay} секунд")
        await asyncio.sleep(delay)

        # Спроба перепідключення
        if await self.connect(connection_id):
            # Відновлення підписок
            subscriptions = self._subscriptions.get(connection_id, set()).copy()
            for channel in subscriptions:
                handler = self._message_handlers.get(f"{connection_id}:{channel}")
                if handler:
                    await self.subscribe(connection_id, channel, handler) 