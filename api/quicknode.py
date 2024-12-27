"""QuickNode API wrapper"""

import os
import json
import base58
import aiohttp
import ssl
from loguru import logger
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from decimal import Decimal
from typing import Optional

class QuicknodeAPI:
    def __init__(self):
        self.endpoint = os.getenv('QUICKNODE_HTTP_URL')
        self.jupiter_endpoint = 'https://cache.jup.ag/tokens'
        if not self.endpoint:
            raise ValueError("QUICKNODE_HTTP_URL не знайдено в змінних середовища")
            
        self.headers = {
            "Content-Type": "application/json",
        }
        # Створюємо SSL контекст
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
        # Створюємо постійний конектор
        self.connector = aiohttp.TCPConnector(ssl=self.ssl_context)
        self.session = aiohttp.ClientSession(connector=self.connector)
        
        # Кеш для токенів
        self.token_cache = {}
        
    async def close(self):
        """Закриття сесії"""
        if not self.session.closed:
            await self.session.close()
            
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        
    async def _make_request(self, method: str, params: list = None, retry_count: int = 3) -> dict:
        """Виконання RPC запиту до QuickNode з повторними спробами"""
        if params is None:
            params = []
            
        for attempt in range(retry_count):
            try:
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": method,
                    "params": params
                }
                
                async with self.session.post(self.endpoint, json=payload, headers=self.headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Помилка QuickNode API ({response.status}): {error_text}")
                        continue
                        
                    result = await response.json()
                    if "error" in result:
                        logger.error(f"Помилка QuickNode RPC: {result['error']}")
                        continue
                        
                    return result.get("result")
                    
            except Exception as e:
                logger.error(f"Спроба {attempt + 1}/{retry_count}: Помилка запиту до QuickNode: {str(e)}")
                if attempt == retry_count - 1:
                    logger.error("Вичерпано всі спроби запиту до QuickNode")
                    return None
                    
        return None
        
    async def verify_token(self, token_address: str) -> bool:
        """Перевірка існування токена в мережі Solana"""
        try:
            # Перевіряємо чи це валідна Solana адреса
            try:
                token_pubkey = Pubkey.from_string(token_address)
            except Exception as e:
                logger.error(f"Невалідна Solana адреса: {e}")
                return False
                
            # Спочатку перевіряємо через getTokenSupply (швидший метод)
            supply_result = await self._make_request(
                "getTokenSupply",
                [str(token_pubkey)]
            )
            
            if supply_result and "value" in supply_result:
                logger.info(f"Знайдено SPL токен через getTokenSupply: {token_address}")
                return True
                
            # Якщо getTokenSupply не спрацював, перевіряємо через getAccountInfo
            result = await self._make_request(
                "getAccountInfo",
                [str(token_pubkey), {"encoding": "jsonParsed", "commitment": "confirmed"}]
            )
            
            if not result:
                logger.warning(f"Токен {token_address} не знайдено в мережі")
                return False
                
            # Перевіряємо чи це SPL токен
            if "data" in result:
                data = result["data"]
                if isinstance(data, dict) and data.get("program") == "spl-token":
                    parsed_data = data.get("parsed", {})
                    if parsed_data.get("type") == "mint":
                        logger.info(f"Знайдено SPL токен через getAccountInfo: {token_address}")
                        return True
                        
            logger.warning(f"Адреса {token_address} не є SPL токеном")
            return False
            
        except Exception as e:
            logger.error(f"Помилка перевірки токена: {str(e)}")
            return False
            
    async def get_sol_balance(self, pubkey: str = None) -> float:
        """Отримання балансу SOL"""
        try:
            if not pubkey:
                pubkey = os.getenv('SOLANA_PUBLIC_KEY')
                if not pubkey:
                    raise ValueError("SOLANA_PUBLIC_KEY не знайдено в змінних середовища")
                    
            result = await self._make_request("getBalance", [pubkey])
            if result is not None:
                balance = Decimal(str(result.get("value", 0))) / Decimal("1e9")
                return float(balance)
                
            logger.error("Не вдалося отримати баланс")
            return 0.0
            
        except Exception as e:
            logger.error(f"Помилка отримання балансу: {str(e)}")
            return 0.0
            
    async def get_token_balance(self, token_address: str, owner_address: str = None) -> float:
        """Отримання балансу токена"""
        try:
            if not owner_address:
                owner_address = os.getenv('SOLANA_PUBLIC_KEY')
                if not owner_address:
                    raise ValueError("SOLANA_PUBLIC_KEY не знайдено в змінних середовища")
                    
            # Отримуємо токен аккаунт
            result = await self._make_request(
                "getTokenAccountsByOwner",
                [
                    owner_address,
                    {"mint": token_address},
                    {"encoding": "jsonParsed"}
                ]
            )
            
            if not result or "value" not in result:
                return 0.0
                
            for account in result["value"]:
                if "account" in account and "data" in account["account"]:
                    data = account["account"]["data"]
                    if isinstance(data, dict) and "parsed" in data:
                        info = data["parsed"]["info"]
                        token_amount = info.get("tokenAmount", {})
                        amount = Decimal(str(token_amount.get("amount", 0)))
                        decimals = int(token_amount.get("decimals", 0))
                        if amount > 0:
                            return float(amount / Decimal(str(10 ** decimals)))
                            
            return 0.0
            
        except Exception as e:
            logger.error(f"Помилка отримання балансу токена: {e}")
            return 0.0
            
    async def get_token_info(self, mint_address: str) -> dict:
        """Отримання інформації про токен через Jupiter API"""
        try:
            # Перевіряємо кеш
            if mint_address in self.token_cache:
                return self.token_cache[mint_address]
                
            # Отримуємо список сіх токенів
            async with self.session.get(self.jupiter_endpoint) as response:
                if response.status != 200:
                    logger.error(f"Помилка отримання списку токенів: {response.status}")
                    return None
                    
                tokens = await response.json()
                
            # Шукаємо потрібний токен
            token_info = next(
                (token for token in tokens if token.get('address') == mint_address),
                None
            )
            
            if token_info:
                # Зберігаємо в кеш
                self.token_cache[mint_address] = token_info
                return token_info
                
            return None
            
        except Exception as e:
            logger.error(f"Помилка отримання інформації про токен: {e}")
            return None
            
    async def get_all_tokens(self, owner_address: str = None) -> list:
        """Отримання всіх токенів на гаманці"""
        try:
            if not owner_address:
                owner_address = os.getenv('SOLANA_PUBLIC_KEY')
                if not owner_address:
                    raise ValueError("SOLANA_PUBLIC_KEY не знайдено в змінних середовища")
                    
            # Отримуємо всі токен аккаунти
            result = await self._make_request(
                "getTokenAccountsByOwner",
                [
                    owner_address,
                    {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
                    {"encoding": "jsonParsed"}
                ]
            )
            
            if not result or "value" not in result:
                return []
                
            tokens = []
            # Додаємо SOL
            sol_balance = await self.get_sol_balance(owner_address)
            tokens.append({
                "mint": "So11111111111111111111111111111111111111112",
                "balance": sol_balance,
                "decimals": 9,
                "symbol": "SOL",
                "name": "Solana",
                "icon": "https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/So11111111111111111111111111111111111111112/logo.png"
            })
            
            # Отримуємо список всіх токенів з Jupiter API
            async with self.session.get(self.jupiter_endpoint) as response:
                if response.status == 200:
                    jupiter_tokens = await response.json()
                    jupiter_tokens_map = {token['address']: token for token in jupiter_tokens}
                else:
                    jupiter_tokens_map = {}

            # Обробляємо кожен токен аккаунт
            for account in result["value"]:
                try:
                    if "account" in account and "data" in account["account"]:
                        data = account["account"]["data"]
                        if isinstance(data, dict) and "parsed" in data:
                            info = data["parsed"]["info"]
                            mint = info.get("mint")
                            token_amount = info.get("tokenAmount", {})
                            amount = Decimal(str(token_amount.get("amount", 0)))
                            decimals = int(token_amount.get("decimals", 0))
                            
                            if amount > 0:
                                balance = float(amount / Decimal(str(10 ** decimals)))
                                
                                # Отримуємо додаткову інформацію з Jupiter API
                                token_info = jupiter_tokens_map.get(mint, {})
                                
                                tokens.append({
                                    "mint": mint,
                                    "balance": balance,
                                    "decimals": decimals,
                                    "symbol": token_info.get("symbol", "Unknown"),
                                    "name": token_info.get("name", "Unknown Token"),
                                    "icon": token_info.get("logoURI", "")
                                })
                except Exception as e:
                    logger.error(f"Помилка обробки токен аккаунта: {e}")
                    continue
            
            return tokens
            
        except Exception as e:
            logger.error(f"Помилка отримання токенів: {e}")
            return []
            
    async def get_transaction_status(self, signature: str) -> Optional[str]:
        """Отримання статусу транзакції"""
        try:
            logger.debug(f"Перевірка статусу транзакції {signature}")
            
            # Спочатку пробуємо через getTransaction
            logger.debug("Спроба через getTransaction...")
            tx_result = await self._make_request(
                "getTransaction",
                [str(signature), {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}]
            )
            
            if tx_result:
                if "meta" in tx_result and tx_result["meta"] is not None:
                    if tx_result["meta"].get("err") is None:
                        return "confirmed"
                    else:
                        return "failed"
                        
            # Якщо не вдалося, пробуємо через getSignatureStatuses
            logger.debug("Спроба через getSignatureStatuses...")
            status_result = await self._make_request(
                "getSignatureStatuses",
                [[str(signature)]]
            )
            
            if status_result and "value" in status_result:
                status = status_result["value"][0]
                if status is None:
                    return "pending"
                elif status.get("err") is None:
                    return "confirmed"
                else:
                    return "failed"
                    
            logger.warning(f"Не вдалося отримати статус транзакції {signature}")
            return "pending"
            
        except Exception as e:
            logger.error(f"Помилка отримання статусу транзакції: {str(e)}")
            return None 