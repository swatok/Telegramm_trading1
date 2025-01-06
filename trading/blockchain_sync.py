"""
Модуль для синхронізації з блокчейном.
Відповідає за отримання та відстеження стану транзакцій.
"""

from typing import Optional, Dict, List
import asyncio
from datetime import datetime

from .constants import CONFIRMATION_TIMEOUT
from ..api.quicknode import QuickNodeAPI
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class BlockchainSync:
    """
    Клас для синхронізації з блокчейном.
    Відстежує стан транзакцій та оновлює їх статус.
    """

    def __init__(self, quicknode_api: QuickNodeAPI):
        """
        Ініціалізація синхронізатора.

        Args:
            quicknode_api: Екземпляр API QuickNode
        """
        self.quicknode_api = quicknode_api
        self._pending_transactions: Dict[str, Dict] = {}
        self._sync_active = False
        self._last_block: Optional[int] = None

    async def start_sync(self, interval: int = 2):
        """
        Запуск синхронізації з блокчейном.

        Args:
            interval: Інтервал оновлення в секундах
        """
        self._sync_active = True
        while self._sync_active:
            try:
                await self._sync_transactions()
                await self._update_block_height()
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Помилка синхронізації: {e}")
                await asyncio.sleep(5)

    async def stop_sync(self):
        """Зупинка синхронізації."""
        self._sync_active = False

    async def add_transaction(self, tx_hash: str, metadata: Dict = None):
        """
        Додавання транзакції для відстеження.

        Args:
            tx_hash: Хеш транзакції
            metadata: Додаткові дані про транзакцію
        """
        self._pending_transactions[tx_hash] = {
            'status': 'pending',
            'timestamp': datetime.now(),
            'confirmations': 0,
            'metadata': metadata or {}
        }

    async def _sync_transactions(self):
        """Синхронізація статусу всіх відстежуваних транзакцій."""
        for tx_hash in list(self._pending_transactions.keys()):
            tx_data = self._pending_transactions[tx_hash]
            if (datetime.now() - tx_data['timestamp']).seconds > CONFIRMATION_TIMEOUT:
                logger.warning(f"Транзакція {tx_hash} перевищила таймаут")
                self._pending_transactions.pop(tx_hash)
                continue

            try:
                status = await self.quicknode_api.get_transaction_status(tx_hash)
                if status['confirmed']:
                    tx_data['status'] = 'confirmed'
                    tx_data['confirmations'] = status['confirmations']
                    if status['confirmations'] >= 1:
                        logger.info(f"Транзакція {tx_hash} підтверджена")
                        self._pending_transactions.pop(tx_hash)
            except Exception as e:
                logger.error(f"Помилка перевірки транзакції {tx_hash}: {e}")

    async def _update_block_height(self):
        """Оновлення висоти блоку."""
        try:
            current_block = await self.quicknode_api.get_block_height()
            if self._last_block and current_block > self._last_block:
                await self._process_new_blocks(self._last_block + 1, current_block)
            self._last_block = current_block
        except Exception as e:
            logger.error(f"Помилка оновлення висоти блоку: {e}")

    async def _process_new_blocks(self, start_block: int, end_block: int):
        """
        Обробка нових блоків.

        Args:
            start_block: Початковий блок
            end_block: Кінцевий блок
        """
        try:
            blocks = await self.quicknode_api.get_blocks_range(start_block, end_block)
            for block in blocks:
                await self._process_block(block)
        except Exception as e:
            logger.error(f"Помилка обробки блоків {start_block}-{end_block}: {e}")

    async def _process_block(self, block: Dict):
        """
        Обробка окремого блоку.

        Args:
            block: Дані блоку
        """
        for tx in block.get('transactions', []):
            if tx['hash'] in self._pending_transactions:
                await self._update_transaction_status(tx['hash'], block['number'])

    async def _update_transaction_status(self, tx_hash: str, block_number: int):
        """
        Оновлення статусу транзакції.

        Args:
            tx_hash: Хеш транзакції
            block_number: Номер блоку
        """
        if tx_hash in self._pending_transactions:
            confirmations = self._last_block - block_number + 1
            self._pending_transactions[tx_hash].update({
                'status': 'confirmed',
                'confirmations': confirmations,
                'block_number': block_number
            }) 