"""Jupiter API wrapper"""

import os
import json
import aiohttp
from loguru import logger
from solders.keypair import Keypair
from decimal import Decimal

class JupiterAPI:
    def __init__(self):
        self.base_url = "https://quote-api.jup.ag/v6"
        self.price_url = "https://price.jup.ag/v4"
        self.headers = {"Content-Type": "application/json"}
        self._session = None
        
    @property
    def session(self):
        """Отримання активної сесії"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
        
    async def close(self):
        """Закриття сесії"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
            
    async def verify_token(self, token_address: str) -> bool:
        """Перевірка чи торгується токен на Jupiter"""
        try:
            # Спочатку перевіряємо через quote API з мінімальною сумою
            test_quote_params = {
                "inputMint": "So11111111111111111111111111111111111111112",  # SOL
                "outputMint": token_address,
                "amount": "100000",  # 0.0001 SOL
                "slippageBps": 50
            }
            
            url = f"{self.base_url}/quote"
            async with self.session.get(url, params=test_quote_params) as response:
                response_text = await response.text()
                logger.debug(f"Відповідь від Jupiter quote API: {response_text}")
                
                if response.status == 200:
                    quote_data = await response.json()
                    if not quote_data.get("error"):
                        logger.info(f"Токен {token_address} доступний для свопу на Jupiter")
                        return True
                        
            # Якщо через quote не знайшли, перевіряємо через price API
            url = f"{self.price_url}/price?ids={token_address}"
            async with self.session.get(url) as response:
                response_text = await response.text()
                logger.debug(f"Відповідь від Jupiter price API: {response_text}")
                
                if response.status == 200:
                    price_data = await response.json()
                    if price_data.get("data", {}).get(token_address):
                        logger.info(f"Токен {token_address} має ціну на Jupiter")
                        return True
                        
            logger.warning(f"Токен {token_address} не знайдено на Jupiter")
            return False
                    
        except Exception as e:
            logger.error(f"Помилка перевірки токена: {str(e)}")
            await self.close()  # Закриваємо сесію при помилці
            return False
            
    async def get_quote(self, input_mint: str, output_mint: str, amount: float, slippage_bps: int = 50) -> dict:
        """Отримання котирування та перевірка можливості торгівлі"""
        try:
            logger.info(f"Запит котирування: {input_mint} -> {output_mint}, сума: {amount}")
            
            # Конвертуємо SOL в ламопорти
            amount_lamports = int(Decimal(str(amount)) * Decimal("1e9"))
            
            params = {
                "inputMint": input_mint,
                "outputMint": output_mint,
                "amount": str(amount_lamports),
                "slippageBps": slippage_bps,
                "onlyDirectRoutes": False,
                "asLegacyTransaction": False,
                "platformFeeBps": 0,
                "maxAccounts": 10
            }
            
            url = f"{self.base_url}/quote"
            async with self.session.get(url, params=params) as response:
                response_text = await response.text()
                logger.debug(f"Відповідь від Jupiter: {response_text}")
                
                if response.status == 404:
                    logger.warning(f"Токен {output_mint} не знайдено на Jupiter")
                    return None
                    
                if response.status != 200:
                    logger.error(f"Помилка API Jupiter ({response.status}): {response_text}")
                    return None
                    
                quote = await response.json()
                if quote.get("error"):
                    logger.warning(f"Помилка отримання котирування: {quote['error']}")
                    return None
                    
                logger.debug(f"Отримано котирування: {json.dumps(quote, indent=2)}")
                return quote
                    
        except Exception as e:
            logger.error(f"Помилка отримання котирування: {str(e)}")
            await self.close()  # Закриваємо сесію при помилці
            return None
            
    async def sign_and_send(self, quote: dict, keypair: Keypair) -> str:
        """Підписання та відправка транзакції"""
        try:
            logger.info("Підготовка транзакції свопу")
            
            # Крок 1: Отримуємо транзакцію
            url = f"{self.base_url}/swap"
            swap_params = {
                "quoteResponse": quote,
                "userPublicKey": str(keypair.pubkey()),
                "wrapUnwrapSOL": True,
                "computeUnitPriceMicroLamports": 1000  # Оптимізація комісії
            }
            
            async with self.session.post(url, json=swap_params, headers=self.headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Помилка отримання транзакції ({response.status}): {error_text}")
                    return None
                    
                swap_response = await response.json()
                if not swap_response.get('swapTransaction'):
                    logger.error("Відсутні дані транзакції в відповіді")
                    return None
                    
                # Крок 2: Підписуємо транзакцію
                tx_data = bytes.fromhex(swap_response['swapTransaction'])
                signed_tx = keypair.sign_message(tx_data)
                
                # Крок 3: Відправляємо підписану транзакцію
                url = "https://api.mainnet-beta.solana.com"  # Використовуємо основний RPC
                send_params = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "sendTransaction",
                    "params": [
                        signed_tx.hex(),
                        {"encoding": "hex", "skipPreflight": True, "preflightCommitment": "confirmed"}
                    ]
                }
                
                async with self.session.post(url, json=send_params, headers=self.headers) as send_response:
                    if send_response.status != 200:
                        error_text = await send_response.text()
                        logger.error(f"Помилка відправки транзакції ({send_response.status}): {error_text}")
                        return None
                        
                    result = await send_response.json()
                    if "error" in result:
                        logger.error(f"Помилка відправки транзакції: {result['error']}")
                        return None
                        
                    signature = result.get("result")
                    if signature:
                        logger.info(f"Транзакція успішно відправлена: {signature}")
                        return signature
                    return None
                    
        except Exception as e:
            logger.error(f"Помилка підписання/відправки транзакції: {str(e)}")
            await self.close()  # Закриваємо сесію при помилці
            return None