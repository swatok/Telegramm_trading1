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
from typing import Optional, List, Dict
from dotenv import load_dotenv
from solana.rpc.api import Client
import base64

# Константи
TOKEN_PROGRAM_ID = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"

class QuicknodeAPI:
    def __init__(self, ssl_context=None):
        """Ініціалізація API клієнта"""
        self.http_url = os.getenv('QUICKNODE_HTTP_URL')
        self.ws_url = os.getenv('QUICKNODE_WS_URL')
        if not self.http_url or not self.ws_url:
            raise ValueError("Не вказані URL для QuickNode")
            
        self.session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=False if ssl_context is None else ssl_context)
        )
        
        try:
            # Отримуємо URL з .env
            load_dotenv()
            self.http_url = os.getenv('QUICKNODE_HTTP_URL')
            self.ws_url = os.getenv('QUICKNODE_WS_URL')
            self.jupiter_endpoint = "https://token.jup.ag/all"
            
            if not self.http_url or not self.ws_url:
                raise ValueError("Відсутні QUICKNODE_HTTP_URL або QUICKNODE_WS_URL")
                
            # Ініціалізуємо клієнт
            self.client = Client(self.http_url, commitment="confirmed")
            
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
            
            # Кеш для токенів
            self.token_info_cache = {}
            
            # URL для RPC запит��в
            self.rpc_url = self.http_url
            
        except Exception as e:
            logger.error(f"Помилка ініціалізації QuicknodeAPI: {e}")
            raise
            
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
                        logger.error(f"Поми��ка QuickNode API ({response.status}): {error_text}")
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
        
    async def verify_token(self, token_address: str) -> Optional[Dict]:
        """Перевірка існування токена"""
        try:
            logger.info(f"Перевірка токена {token_address}")
            
            # Спочатку перевіряємо через Jupiter API
            token_info = await self.get_token_info(token_address)
            if token_info:
                logger.info(f"Токен знайдено в Jupiter API: {token_info}")
                return token_info
                
            # Якщо токен не знайдено в Jupiter API, перевіряємо через Solana
            logger.info("Перевірка токена через Solana...")
            
            # Формуємо запит до Solana RPC
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getAccountInfo",
                "params": [
                    token_address,
                    {"encoding": "jsonParsed", "commitment": "confirmed"}
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.rpc_url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.debug(f"Відповідь від Solana RPC: {data}")
                        
                        if "result" in data and data["result"]:
                            logger.info("Токен існує в мережі Solana")
                            
                            # Спробуємо отримати додаткову інформацію про токен
                            token_info = {
                                "address": token_address,
                                "exists": True,
                                "source": "solana"
                            }
                            
                            # Додаємо інформацію про метадані, якщо вони є
                            if "data" in data["result"] and "parsed" in data["result"]["data"]:
                                parsed_data = data["result"]["data"]["parsed"]
                                if "info" in parsed_data:
                                    token_info.update({
                                        "decimals": parsed_data["info"].get("decimals", 9),
                                        "supply": parsed_data["info"].get("supply"),
                                        "name": parsed_data["info"].get("name", "Unknown"),
                                        "symbol": parsed_data["info"].get("symbol", "Unknown")
                                    })
                            
                            logger.info(f"Отримано інформацію про токен: {token_info}")
                            return token_info
                        else:
                            logger.warning("Токен не знайден�� в мережі Solana")
                            return None
                    else:
                        error_text = await response.text()
                        logger.error(f"Помилка перевірки токена. Статус: {response.status}, Помилка: {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Помилка при перевірці токена: {str(e)}")
            return None
            
    async def get_sol_balance(self) -> Optional[float]:
        """Отримання балансу SOL"""
        try:
            wallet_address = os.getenv('SOLANA_PUBLIC_KEY')
            if not wallet_address:
                raise ValueError("SOLANA_PUBLIC_KEY не знайдено в змінних середовища")
                
            response = await self._make_request(
                "getBalance",
                [wallet_address]
            )
            
            if response and "value" in response:
                return float(response["value"]) / 1e9  # Конвертуємо лампорти в SOL
            return None
            
        except Exception as e:
            logger.error(f"Помилка отримання балансу SOL: {e}")
            return None
            
    async def get_token_balance(self, token_address: str) -> Optional[float]:
        """Отримання балансу токена"""
        try:
            owner_address = os.getenv('SOLANA_PUBLIC_KEY')
            if not owner_address:
                raise ValueError("SOLANA_PUBLIC_KEY не знайдено в змінних середовища")
                
            # Отримуємо всі токен аккаунти
            response = await self._make_request(
                "getTokenAccountsByOwner",
                [
                    owner_address,
                    {"mint": token_address},
                    {"encoding": "jsonParsed"}
                ]
            )
            
            if not response or "value" not in response:
                return 0.0
                
            # Якщо немає акаунтів
            if not response["value"]:
                return 0.0
                
            # Беремо перший аккаунт
            account = response["value"][0]
            if "account" not in account or "data" not in account["account"]:
                return 0.0
                
            data = account["account"]["data"]
            if not isinstance(data, dict) or "parsed" not in data:
                return 0.0
                
            info = data["parsed"].get("info", {})
            token_amount = info.get("tokenAmount", {})
            
            amount = token_amount.get("amount", "0")
            decimals = token_amount.get("decimals", 9)
            
            return float(amount) / (10 ** decimals)
            
        except Exception as e:
            logger.error(f"Помилка отримання балансу токена: {e}")
            return None
            
    async def get_token_info(self, token_address: str) -> Optional[Dict]:
        """Отримання інформації про токен"""
        try:
            logger.info(f"Отримання інформації про токен {token_address} з Jupiter API")
            
            # Спочатку перевіряємо кеш
            if token_address in self.token_info_cache:
                logger.info(f"Знайдено інформацію про токен в кеші: {self.token_info_cache[token_address]}")
                return self.token_info_cache[token_address]
            
            # Отримуємо список всіх токенів з Jupiter API
            async with self.session.get(self.jupiter_endpoint) as response:
                if response.status == 200:
                    tokens = await response.json()
                    logger.info(f"Отримано {len(tokens)} токенів з Jupiter API")
                    
                    # Шукаємо наш токен
                    for token in tokens:
                        if token.get("address") == token_address:
                            token_info = {
                                "symbol": token.get("symbol", "Unknown"),
                                "name": token.get("name", "Unknown"),
                                "decimals": token.get("decimals", 9),
                                "logo": token.get("logoURI"),
                                "source": "jupiter"
                            }
                            logger.info(f"Знайдено токен в Jupiter API: {token_info}")
                            
                            # Зберігаємо в кеш
                            self.token_info_cache[token_address] = token_info
                            return token_info
                            
            # Якщо токен не знайдено в Jupiter API, перевіряємо через Solana
            logger.info("Токен не знайдено в Jupiter API, перевіряємо через Solana...")
            
            # Формуємо запит до Solana RPC
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getAccountInfo",
                "params": [
                    token_address,
                    {"encoding": "jsonParsed", "commitment": "confirmed"}
                ]
            }
            
            async with self.session.post(self.rpc_url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.debug(f"Відповідь від Solana RPC: {data}")
                    
                    if "result" in data and data["result"]:
                        logger.info("Токен існує в мережі Solana")
                        
                        # Отримуємо інформацію про токен
                        token_info = {
                            "address": token_address,
                            "exists": True,
                            "source": "solana"
                        }
                        
                        # Додаємо інформацію про метадані, якщо вони є
                        if "data" in data["result"] and "parsed" in data["result"]["data"]:
                            parsed_data = data["result"]["data"]["parsed"]
                            if "info" in parsed_data:
                                token_info.update({
                                    "decimals": parsed_data["info"].get("decimals", 9),
                                    "supply": parsed_data["info"].get("supply"),
                                    "name": parsed_data["info"].get("name", "Unknown"),
                                    "symbol": parsed_data["info"].get("symbol", "Unknown")
                                })
                        
                        logger.info(f"Отримано інформацію про токен через Solana: {token_info}")
                        
                        # Зберігаємо в кеш
                        self.token_info_cache[token_address] = token_info
                        return token_info
                    else:
                        logger.warning("Токен не знайдено в мережі Solana")
                        return None
                else:
                    error_text = await response.text()
                    logger.error(f"Помилка отримання інформації про токен. Статус: {response.status}, Помилка: {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Помилка при отриманні інформації про токен: {str(e)}")
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
            
            response = await self.client.get_signature_statuses([signature])
            if not response:
                logger.warning(f"Не вдалося отримати статус транзакції {signature}")
                return None
                
            status = response.value[0]
            if not status:
                return "pending"
                
            if status.err:
                logger.error(f"Помилка транзакції: {status.err}")
                return "failed"
                
            if status.confirmationStatus == "finalized":
                return "confirmed"
                
            return "pending"
            
        except Exception as e:
            logger.error(f"Помилка перевірки статусу транзакції: {e}")
            return None
            
    async def get_token_accounts(self, wallet_address: str = None) -> List[Dict]:
        """Отримання списку токенів на гаманці"""
        try:
            if not wallet_address:
                wallet_address = os.getenv('SOLANA_PUBLIC_KEY')
                if not wallet_address:
                    raise ValueError("SOLANA_PUBLIC_KEY не знайдено в змінних середовища")
            
            # Отримуємо баланс SOL
            sol_balance = await self.get_sol_balance()
            tokens = []
            
            # Додаємо SOL до списку токенів
            if sol_balance is not None:
                tokens.append({
                    'mint': 'So11111111111111111111111111111111111111112',
                    'symbol': 'SOL',
                    'name': 'Solana',
                    'balance': sol_balance,
                    'decimals': 9,
                    'value': sol_balance,
                    'logo': 'https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/So11111111111111111111111111111111111111112/logo.png'
                })
            
            # Отримуємо список токенів з Jupiter API
            try:
                async with self.session.get(self.jupiter_endpoint) as response:
                    if response.status == 200:
                        jupiter_tokens = await response.json()
                        jupiter_tokens_map = {token['address']: token for token in jupiter_tokens}
                    else:
                        jupiter_tokens_map = {}
            except Exception as e:
                logger.error(f"Помилка отримання списку токенів з Jupiter: {e}")
                jupiter_tokens_map = {}
            
            # Отримуємо токен аккаунти
            response = await self._make_request(
                "getTokenAccountsByOwner",
                [
                    wallet_address,
                    {"programId": TOKEN_PROGRAM_ID},
                    {"encoding": "jsonParsed"}
                ]
            )
            
            if not response or "value" not in response:
                logger.error("Не вдалося отримати токени")
                return tokens
            
            for item in response["value"]:
                try:
                    if "account" not in item or "data" not in item["account"]:
                        continue
                    
                    data = item["account"]["data"]
                    if not isinstance(data, dict) or "parsed" not in data:
                        continue
                    
                    info = data["parsed"].get("info", {})
                    if not info:
                        continue
                        
                    mint = info.get("mint")
                    token_amount = info.get("tokenAmount", {})
                    
                    if not mint or not token_amount:
                        continue
                    
                    amount = token_amount.get("amount", "0")
                    decimals = token_amount.get("decimals", 9)
                    balance = float(amount) / (10 ** decimals)
                    
                    # Пропускаємо токени з нульовим балансом
                    if balance <= 0:
                        continue
                    
                    # Отримуємо інформацію про токен
                    jupiter_token = jupiter_tokens_map.get(mint, {})
                    token_info = await self.get_token_info(mint) or {}
                    
                    token_data = {
                        'mint': mint,
                        'symbol': jupiter_token.get('symbol', token_info.get('symbol', 'Unknown')),
                        'name': jupiter_token.get('name', token_info.get('name', 'Unknown Token')),
                        'balance': balance,
                        'decimals': decimals,
                        'value': balance * jupiter_token.get('price', 0),  # Вартість в SOL
                        'logo': jupiter_token.get('logoURI', '')
                    }
                    
                    tokens.append(token_data)
                    
                except Exception as e:
                    logger.error(f"Помилка обробки токена: {e}")
                    continue
            
            return tokens
            
        except Exception as e:
            logger.error(f"Помилка отримання токенів: {e}")
            return [] 
            
    async def verify_transaction(self, signature: str) -> bool:
        """Перевірка статусу транзакції"""
        try:
            result = await self._make_request(
                "getSignatureStatuses",
                [[signature], {"searchTransactionHistory": True}]
            )
            
            if not result or not result.get("value"):
                return False
                
            status = result["value"][0]
            if not status:
                return False
                
            # Перевіряємо чи транзакція підтверджена
            if status.get("confirmationStatus") == "finalized":
                # Отримуємо деталі транзакції
                tx_details = await self._make_request(
                    "getTransaction",
                    [signature, {"encoding": "jsonParsed"}]
                )
                
                if tx_details and tx_details.get("meta", {}).get("err") is None:
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"Помилка перевірки транзакції {signature}: {e}")
            return False 