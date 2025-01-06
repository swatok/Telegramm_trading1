"""
Менеджер балансів гаманця
"""

import asyncio
from decimal import Decimal
from typing import Dict, Optional, List
from loguru import logger

from .constants import BALANCE_MIN, TOKEN_ADDRESS
from api.quicknode import QuickNodeAPI
from api.jupiter import JupiterAPI

class WalletBalanceManager:
    """Менеджер для управління балансами гаманця"""
    
    def __init__(
        self,
        quicknode_api: QuickNodeAPI,
        jupiter_api: JupiterAPI,
        wallet_address: str
    ):
        self.quicknode_api = quicknode_api
        self.jupiter_api = jupiter_api
        self.wallet_address = wallet_address
        self._balances: Dict[str, Decimal] = {}
        self._update_lock = asyncio.Lock()
        
    async def update_balances(self):
        """Оновлення балансів всіх токенів"""
        async with self._update_lock:
            try:
                # Оновлення балансу SOL
                sol_balance = await self.quicknode_api.get_sol_balance(self.wallet_address)
                self._balances['SOL'] = Decimal(str(sol_balance))
                
                # Оновлення балансу WSOL
                wsol_balance = await self.quicknode_api.get_token_balance(
                    self.wallet_address,
                    TOKEN_ADDRESS
                )
                self._balances['WSOL'] = Decimal(str(wsol_balance))
                
                logger.info("Баланси оновлено успішно")
            except Exception as e:
                logger.error(f"Помилка оновлення балансів: {e}")
                
    async def get_balance(self, token: str = 'SOL') -> Optional[Decimal]:
        """
        Отримання балансу конкретного токену
        
        Args:
            token: Символ токену
            
        Returns:
            Баланс токену або None у разі помилки
        """
        if token not in self._balances:
            await self.update_balances()
        return self._balances.get(token)
        
    async def has_sufficient_balance(self, amount: Decimal, token: str = 'SOL') -> bool:
        """
        Перевірка достатності балансу
        
        Args:
            amount: Необхідна кількість
            token: Символ токену
            
        Returns:
            True якщо баланс достатній, False інакше
        """
        balance = await self.get_balance(token)
        if balance is None:
            return False
            
        # Для SOL враховуємо мінімальний баланс
        if token == 'SOL':
            return balance >= (amount + BALANCE_MIN)
        return balance >= amount
        
    async def get_total_balance(self) -> Optional[Dict]:
        """
        Отримання повного балансу гаманця з розрахунком вартості в SOL
        
        Returns:
            Словник з балансами та вартістю або None у разі помилки
        """
        try:
            # Оновлюємо баланси
            await self.update_balances()
            
            # Отримуємо токен-акаунти
            token_accounts = await self.quicknode_api.get_token_accounts(self.wallet_address)
            tokens = []
            total_value_sol = self._balances['SOL']
            
            # Обробляємо кожен токен
            for account in token_accounts:
                try:
                    token_address = account['mint']
                    if not token_address or token_address == TOKEN_ADDRESS:
                        continue
                        
                    # Отримуємо баланс і decimals
                    raw_amount = Decimal(str(account['amount']))
                    decimals = int(account['decimals'])
                    token_balance = raw_amount / Decimal(str(10 ** decimals))
                    
                    if token_balance <= 0:
                        continue
                        
                    # Отримуємо інформацію про токен та ціну
                    token_info = await self.jupiter_api.get_token_info(token_address)
                    price_in_sol = await self.jupiter_api.get_price(token_address, TOKEN_ADDRESS)
                    
                    if token_info and price_in_sol:
                        price_decimal = Decimal(str(price_in_sol))
                        value_in_sol = token_balance * price_decimal
                        total_value_sol += value_in_sol
                        
                        tokens.append({
                            "address": token_address,
                            "symbol": token_info.get("symbol", "Unknown"),
                            "name": token_info.get("name", "Unknown Token"),
                            "balance": float(token_balance),
                            "price_sol": float(price_decimal),
                            "value_sol": float(value_in_sol)
                        })
                        
                except Exception as e:
                    logger.error(f"Помилка обробки токену {token_address}: {str(e)}")
                    continue
                    
            return {
                "sol_balance": float(self._balances['SOL']),
                "total_value_sol": float(total_value_sol),
                "tokens": tokens
            }
            
        except Exception as e:
            logger.error(f"Помилка отримання повного балансу: {str(e)}")
            return None 