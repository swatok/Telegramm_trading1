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

class QuicknodeAPI:
    def __init__(self):
        self.endpoint = os.getenv('QUICKNODE_HTTP_URL')
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
            
    async def get_transaction_status(self, signature: str, wait_confirmation: bool = True) -> dict:
        """Отримання статусу транзакції з очікуванням підтвердження"""
        try:
            if wait_confirmation:
                # Чекаємо підтвердження транзакції
                confirm_result = await self._make_request(
                    "confirmTransaction",
                    [signature, {"commitment": "confirmed"}]
                )
                if not confirm_result or not confirm_result.get("value", {}).get("value"):
                    logger.warning(f"Транзакція {signature} не підтверджена")
                    return {'confirmed': False, 'error': True}
                    
            # Отримуємо деталі транзакції
            result = await self._make_request(
                "getSignatureStatuses",
                [[signature]]
            )
            
            if result and "value" in result and result["value"][0]:
                status = result["value"][0]
                confirmation_status = status.get('confirmationStatus')
                return {
                    'confirmed': confirmation_status == 'confirmed' or confirmation_status == 'finalized',
                    'error': status.get('err') is not None,
                    'confirmations': status.get('confirmations'),
                    'status': confirmation_status
                }
                
            return {'confirmed': False, 'error': True, 'confirmations': 0, 'status': 'unknown'}
            
        except Exception as e:
            logger.error(f"Помилка отримання статусу транзакції: {e}")
            return {'confirmed': False, 'error': True, 'confirmations': 0, 'status': 'error'} 