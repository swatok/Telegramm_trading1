"""
Модуль для низькорівневого моніторингу цін через WebSocket QuickNode.
"""

import json
import aiohttp
import asyncio
from typing import List, Dict, Optional, Callable
from loguru import logger

from .base import QuickNodeBase

class PriceMonitor(QuickNodeBase):
    """
    Клас для низькорівневого моніторингу цін токенів через WebSocket QuickNode.
    """

    def __init__(self, ws_url: str, token_addresses: List[str], callback: Optional[Callable] = None):
        """
        Ініціалізація монітора цін.

        Args:
            ws_url: URL для WebSocket підключення
            token_addresses: Список адрес токенів для моніторингу
            callback: Функція, яка буде викликана при оновленні ціни
        """
        super().__init__(ws_url)
        self.token_addresses = token_addresses
        self.callback = callback
        self.websocket = None
        self.running = False
        self.reconnect_delay = 1  # Початкова затримка для перепідключення
        self.max_reconnect_delay = 60  # Максимальна затримка

    async def start(self):
        """Запуск моніторингу цін"""
        self.running = True
        while self.running:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(self.ws_url, ssl=self.ssl_context) as websocket:
                        self.websocket = websocket
                        logger.info("WebSocket з'єднання встановлено")
                        
                        # Підписуємося на оновлення для кожного токена
                        for token_address in self.token_addresses:
                            await self._subscribe_to_token(token_address)
                        
                        # Обробляємо вхідні повідомлення
                        async for message in websocket:
                            if message.type == aiohttp.WSMsgType.TEXT:
                                await self._handle_message(message.data)
                            elif message.type == aiohttp.WSMsgType.ERROR:
                                logger.error(f"WebSocket помилка: {message.data}")
                                break
                                
            except aiohttp.ClientError as e:
                logger.error(f"Помилка підключення: {e}")
                await self._handle_reconnect()

    async def stop(self):
        """Зупинка моніторингу цін"""
        self.running = False
        if self.websocket:
            await self.websocket.close()

    async def _subscribe_to_token(self, token_address: str):
        """
        Підписка на оновлення ціни токена.

        Args:
            token_address: Адреса токену
        """
        subscription = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "accountSubscribe",
            "params": [
                token_address,
                {"encoding": "jsonParsed", "commitment": "confirmed"}
            ]
        }
        await self.websocket.send_json(subscription)
        logger.info(f"Підписано на оновлення токена: {token_address}")

    async def _handle_message(self, message: str):
        """
        Обробка вхідних повідомлень.

        Args:
            message: JSON повідомлення від WebSocket
        """
        try:
            data = json.loads(message)
            if "params" in data and "result" in data["params"]:
                token_data = data["params"]["result"]["value"]
                if self.callback:
                    await self.callback(token_data)
        except json.JSONDecodeError as e:
            logger.error(f"Помилка розбору JSON: {e}")

    async def _handle_reconnect(self):
        """Обробка перепідключення при втраті з'єднання"""
        await asyncio.sleep(self.reconnect_delay)
        self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
        logger.info(f"Спроба перепідключення через {self.reconnect_delay} секунд") 