from typing import Dict, Any, List, Optional
from interfaces import TelegramMonitorInterface
from telethon import TelegramClient, events
import re

class ChannelMonitor(TelegramMonitorInterface):
    """Реалізація інтерфейсу для моніторингу Telegram каналів"""

    def __init__(self, api_id: str, api_hash: str, session_name: str):
        self.client = TelegramClient(session_name, api_id, api_hash)
        self.channels = []
        self.monitoring = False

    async def connect_to_channels(self, channel_ids: List[int]) -> bool:
        """Підключення до каналів моніторингу"""
        try:
            await self.client.start()
            self.channels = channel_ids
            return True
        except Exception as e:
            print(f"Помилка підключення до каналів: {e}")
            return False

    async def parse_message(self, message: str) -> Optional[Dict[str, Any]]:
        """Парсинг повідомлення для виявлення смарт-контрактів"""
        try:
            # Паттерн для пошуку адреси контракту Solana
            contract_pattern = r"([1-9A-HJ-NP-Za-km-z]{32,44})"
            
            # Пошук адреси контракту
            contract_match = re.search(contract_pattern, message)
            if not contract_match:
                return None

            contract_address = contract_match.group(1)
            
            return {
                "contract_address": contract_address,
                "raw_message": message,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Помилка парсингу повідомлення: {e}")
            return None

    async def validate_contract(self, contract_data: Dict[str, Any]) -> bool:
        """Валідація знайденого контракту"""
        try:
            contract_address = contract_data.get("contract_address")
            if not contract_address:
                return False

            # Тут буде логіка валідації контракту
            # Наприклад, перевірка через Solana API
            return True
        except Exception as e:
            print(f"Помилка валідації контракту: {e}")
            return False

    async def start_monitoring(self) -> None:
        """Запуск моніторингу каналів"""
        if not self.client.is_connected():
            await self.client.start()

        @self.client.on(events.NewMessage(chats=self.channels))
        async def handle_new_message(event):
            if not self.monitoring:
                return

            message = event.message.text
            contract_data = await self.parse_message(message)
            
            if contract_data and await self.validate_contract(contract_data):
                # Тут буде логіка обробки знайденого контракту
                pass

        self.monitoring = True
        await self.client.run_until_disconnected()

    async def stop_monitoring(self) -> None:
        """Зупинка моніторингу каналів"""
        self.monitoring = False
        await self.client.disconnect() 