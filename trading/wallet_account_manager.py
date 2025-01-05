"""
Менеджер токен-акаунтів гаманця
"""

from decimal import Decimal
from typing import Dict, Optional, List
from loguru import logger

from api.quicknode import QuickNodeAPI
from api.jupiter import JupiterAPI
from .wallet_balance_manager import WalletBalanceManager

class WalletAccountManager:
    """Менеджер для управління токен-акаунтами гаманця"""
    
    def __init__(
        self,
        quicknode_api: QuickNodeAPI,
        jupiter_api: JupiterAPI,
        wallet_address: str
    ):
        self.quicknode_api = quicknode_api
        self.jupiter_api = jupiter_api
        self.wallet_address = wallet_address
        self.balance_manager = WalletBalanceManager(
            quicknode_api,
            jupiter_api,
            wallet_address
        )
        
    async def wrap_sol(self, amount: Decimal) -> Optional[str]:
        """
        Обгортання SOL в WSOL
        
        Args:
            amount: Кількість SOL для обгортання
            
        Returns:
            Хеш транзакції або None у разі помилки
        """
        try:
            if not await self.balance_manager.has_sufficient_balance(amount):
                logger.error("Недостатньо SOL для обгортання")
                return None
                
            tx_hash = await self.quicknode_api.wrap_sol(
                self.wallet_address,
                amount
            )
            logger.info(f"SOL успішно обгорнуто в WSOL: {tx_hash}")
            return tx_hash
        except Exception as e:
            logger.error(f"Помилка при обгортанні SOL: {e}")
            return None
            
    async def unwrap_sol(self, amount: Decimal) -> Optional[str]:
        """
        Розгортання WSOL в SOL
        
        Args:
            amount: Кількість WSOL для розгортання
            
        Returns:
            Хеш транзакції або None у разі помилки
        """
        try:
            if not await self.balance_manager.has_sufficient_balance(amount, 'WSOL'):
                logger.error("Недостатньо WSOL для розгортання")
                return None
                
            tx_hash = await self.quicknode_api.unwrap_sol(
                self.wallet_address,
                amount
            )
            logger.info(f"WSOL успішно розгорнуто в SOL: {tx_hash}")
            return tx_hash
        except Exception as e:
            logger.error(f"Помилка при розгортанні WSOL: {e}")
            return None
            
    async def get_token_accounts(self) -> List[Dict]:
        """
        Отримання списку токен-акаунтів гаманця
        
        Returns:
            Список токен-акаунтів
        """
        try:
            accounts = await self.quicknode_api.get_token_accounts(self.wallet_address)
            return accounts
        except Exception as e:
            logger.error(f"Помилка отримання токен-акаунтів: {e}")
            return []
            
    async def close_empty_accounts(self) -> List[str]:
        """
        Закриття порожніх токен-акаунтів
        
        Returns:
            Список хешів транзакцій закриття
        """
        try:
            accounts = await self.get_token_accounts()
            tx_hashes = []
            
            for account in accounts:
                if Decimal(str(account['balance'])) == 0:
                    tx_hash = await self.quicknode_api.close_token_account(
                        self.wallet_address,
                        account['address']
                    )
                    if tx_hash:
                        tx_hashes.append(tx_hash)
                        logger.info(f"Закрито порожній акаунт {account['address']}")
                        
            return tx_hashes
        except Exception as e:
            logger.error(f"Помилка закриття порожніх акаунтів: {e}")
            return []
            
    async def create_token_account(self, token_address: str) -> Optional[str]:
        """
        Створення нового токен-акаунту
        
        Args:
            token_address: Адреса токену
            
        Returns:
            Адреса створеного акаунту або None у разі помилки
        """
        try:
            account_address = await self.quicknode_api.create_token_account(
                self.wallet_address,
                token_address
            )
            if account_address:
                logger.info(f"Створено новий токен-акаунт: {account_address}")
            return account_address
        except Exception as e:
            logger.error(f"Помилка створення токен-акаунту: {e}")
            return None 