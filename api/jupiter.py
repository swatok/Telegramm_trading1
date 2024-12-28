"""Jupiter API wrapper"""

import os
import json
import base58
import aiohttp
import ssl
from loguru import logger
from decimal import Decimal
from typing import Optional, Dict, List
from dotenv import load_dotenv
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.message import Message
import base64
import logging

# Константи
WSOL_ADDRESS = "So11111111111111111111111111111111111111112"

class JupiterAPI:
    def __init__(self, ssl_context=None):
        """Ініціалізація API клієнта"""
        # Список API ендпоінтів для котирувань
        self.quote_endpoints = [
            "https://quote-api.jup.ag/v6",
            "https://quote-api.jup.ag/v4",
            "https://jupiter-quote-api.saber.so/v4"
        ]
        
        # Список API ендпоінтів для цін
        self.price_endpoints = [
            "https://price.jup.ag/v4",
            "https://jupiter-price-api.saber.so/v4",
            "https://price-api.jup.ag/v4"
        ]
        
        # Список API ендпоінтів для транзакцій
        self.swap_endpoints = [
            "https://quote-api.jup.ag/v6/swap",
            "https://quote-api.jup.ag/v4/swap"
        ]
        
        # Створюємо SSL контекст
        self.ssl_context = ssl_context or ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
        # Створюємо сесію
        self.session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=self.ssl_context)
        )
        
        self.logger = logging.getLogger(__name__)
        
        # Ініціалізуємо keypair
        private_key = os.getenv('SOLANA_PRIVATE_KEY')
        if not private_key:
            raise ValueError("SOLANA_PRIVATE_KEY не знайдено в змінних середовища")
        private_key_bytes = base58.b58decode(private_key)
        self.keypair = Keypair.from_bytes(private_key_bytes)
        
    async def _try_endpoints(self, endpoints: List[str], endpoint_type: str, params: Dict) -> Optional[Dict]:
        """Спроба використання різних API ендпоінтів"""
        for endpoint in endpoints:
            try:
                url = f"{endpoint}/{endpoint_type}"
                logger.info(f"Спроба використати {endpoint_type} через {endpoint}")
                
                async with self.session.get(url, params=params, ssl=False) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Успішно отримано дані через {endpoint}")
                        return data
                    else:
                        logger.warning(f"Помилка {response.status} при використанні {endpoint}")
                        
            except Exception as e:
                logger.error(f"Помилка при використанні {endpoint}: {str(e)}")
                continue
                
        logger.warning(f"Не вдалося отримати дані через жоден {endpoint_type} ендпоінт")
        return None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Отримання сесії з SSL контекстом"""
        if not self.session or self.session.closed:
            connector = aiohttp.TCPConnector(ssl=self.ssl_context) if self.ssl_context else None
            self.session = aiohttp.ClientSession(connector=connector)
        return self.session
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _sign_and_send_transaction(self, transaction_data: str) -> Optional[Dict]:
        """Підпис та відправка транзакції"""
        try:
            # Декодуємо транзакцію з base64
            tx_bytes = base64.b64decode(transaction_data)
            
            # Створюємо об'єкт транзакції
            tx = Transaction.from_bytes(tx_bytes)
            
            # Підписуємо транзакцію
            tx.sign([self.keypair])
            
            # Серіалізуємо підписану транзакцію
            signed_tx = base64.b64encode(tx.serialize()).decode('utf-8')
            
            # Відправляємо транзакцію
            session = await self._get_session()
            url = f"{self.quote_api_url}/send"
            
            payload = {
                "transaction": signed_tx
            }
            
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "signature": data.get("txid"),
                        "status": "sent"
                    }
                else:
                    logger.error(f"Помилка відправки транзакції ({response.status}): {await response.text()}")
                    return None
                    
        except Exception as e:
            logger.error(f"Помилка підпису та відправки транзакції: {e}")
            return None

    async def get_token_info(self, token_address: str) -> Optional[Dict]:
        """Отримання інформації про токен"""
        try:
            params = {
                "inputMint": WSOL_ADDRESS,
                "outputMint": token_address,
                "amount": "1000000",  # 0.001 SOL
                "slippageBps": 100  # 1%
            }
            
            # Спробуємо отримати інформацію через всі доступні ендпоінти
            data = await self._try_endpoints(self.quote_endpoints, "quote", params)
            
            if data:
                return {
                    "address": token_address,
                    "name": data.get("outputMint", {}).get("name", "Unknown"),
                    "symbol": data.get("outputMint", {}).get("symbol", "Unknown"),
                    "decimals": data.get("outputMint", {}).get("decimals", 9)
                }
            
            logger.warning(f"Не вдалося отримати інформацію про токен через жоден ендпоінт")
            return None
                    
        except Exception as e:
            logger.error(f"Помилка отримання інформації про токен: {e}")
            return None

    async def get_price(self, input_mint: str, output_mint: str = WSOL_ADDRESS) -> Optional[float]:
        """Отримання ціни токена"""
        try:
            params = {
                "ids": input_mint,
                "vsToken": output_mint
            }
            
            # Спробуємо отримати ціну через всі доступні ендпоінти
            data = await self._try_endpoints(self.price_endpoints, "price", params)
            
            if data and "data" in data and input_mint in data["data"]:
                return float(data["data"][input_mint]["price"])
            return None
            
        except Exception as e:
            logger.error(f"Помилка отримання ціни: {e}")
            return None

    async def get_quote(self, input_mint: str, amount: int, output_mint: str, slippage: float = 1.0) -> Optional[Dict]:
        """Отримання котирування для свопу"""
        try:
            logger.info(f"Запит котирування: input_mint={input_mint}, output_mint={output_mint}, amount={amount}, slippage={slippage}")
            
            params = {
                "inputMint": input_mint,
                "outputMint": output_mint,
                "amount": str(amount),
                "slippageBps": int(slippage * 100),
                "onlyDirectRoutes": False,
                "asLegacyTransaction": False,
                "platformFeeBps": 0,
                "maxAccounts": 25,
                "excludeDexes": [],
                "intermediateTokens": True,
                "restrictIntermediateTokens": False,
                "quoteMeta": True
            }
            
            # Виводимо параметри запиту
            print("\nПараметри запиту котирування:")
            print(json.dumps(params, indent=2, ensure_ascii=False))
            
            # Спробуємо отримати котирування через всі доступні ендпоінти
            for endpoint in self.quote_endpoints:
                try:
                    url = f"{endpoint}/quote"
                    logger.info(f"Спроба отримати котирування через {endpoint}")
                    
                    async with self.session.get(url, params=params, ssl=False) as response:
                        response_text = await response.text()
                        
                        # Виводимо відповідь
                        print(f"\nВідповідь від {endpoint}:")
                        try:
                            response_json = json.loads(response_text)
                            print(json.dumps(response_json, indent=2, ensure_ascii=False))
                        except:
                            print(response_text)
                            
                        if response.status == 200:
                            data = json.loads(response_text)
                            if "data" in data:
                                quote_data = data["data"]
                                routes = quote_data.get("routePlan", [])
                                logger.info(f"Знайдено {len(routes)} маршрутів через {endpoint}")
                                
                                if routes:
                                    best_route = routes[0]
                                    logger.info(f"Використовуємо найкращий маршрут через {endpoint}")
                                    logger.info(f"• Ціна: {quote_data.get('price')}")
                                    logger.info(f"• Кількість на виході: {quote_data.get('outAmount')}")
                                    return quote_data
                                    
                except Exception as e:
                    logger.error(f"Помилка при використанні {endpoint}: {str(e)}")
                    continue
                    
            logger.warning("Не вдалося отримати котирування через жоден ендпоінт")
            return None
            
        except Exception as e:
            logger.error(f"Помилка при отриманні котирування: {str(e)}")
            return None

    async def get_swap_transaction(self, quote: Dict) -> Optional[Dict]:
        """Отримання транзакції для свопу"""
        try:
            data = {
                "quoteResponse": quote,
                "userPublicKey": os.getenv('SOLANA_PUBLIC_KEY'),
                "wrapUnwrapSOL": True,
                "asLegacyTransaction": False,
                "computeUnitPriceMicroLamports": 1,
                "prioritizationFeeLamports": 1000
            }
            
            # Спробуємо отримати транзакцію через всі доступні ендпоінти
            for endpoint in self.swap_endpoints:
                try:
                    logger.info(f"Спроба отримати транзакцію через {endpoint}")
                    
                    async with self.session.post(endpoint, json=data, ssl=False) as response:
                        response_text = await response.text()
                        
                        if response.status == 200:
                            swap_data = json.loads(response_text)
                            if 'swapTransaction' in swap_data:
                                logger.info(f"Транзакція успішно отримана через {endpoint}")
                                return swap_data.get('swapTransaction')
                            else:
                                logger.warning(f"Відповідь не містить транзакції: {swap_data}")
                        else:
                            logger.warning(f"Помилка {response.status} при отриманні транзакції через {endpoint}")
                            
                except Exception as e:
                    logger.error(f"Помилка при використанні {endpoint}: {str(e)}")
                    continue
                    
            logger.warning("Не вдалося отримати транзакцію через жоден ендпоінт")
            return None
            
        except Exception as e:
            logger.error(f"Помилка при отриманні транзакції: {str(e)}")
            return None

    async def swap(self, quote: Dict) -> Optional[Dict]:
        """Виконання свопу"""
        try:
            # Отримуємо транзакцію
            transaction = await self.get_swap_transaction(quote)
            if not transaction:
                return None
                
            # Підписуємо та відправляємо транзакцію
            return await self._sign_and_send_transaction(transaction)
                    
        except Exception as e:
            logger.error(f"Помилка виконання свопу: {e}")
            return None

    async def close(self):
        """Закриття сесії"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def check_connection(self) -> bool:
        """Перевірка з'єднання"""
        try:
            url = f"{self.base_url}/quote"
            params = {
                "inputMint": WSOL_ADDRESS,
                "amount": "1000000"  # 0.001 SOL
            }
            
            async with self.session.get(url, params=params) as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"Помилка перевірки з'єднання: {e}")
            return False

    async def check_token_liquidity(self, token_address: str, min_liquidity_sol: float = 1.0) -> bool:
        """Перевірка ліквідності токена"""
        try:
            logger.info(f"Перевірка ліквідності токена {token_address}")
            
            # Спробуємо отримати котирування для різних сум
            test_amounts = [100000, 500000, 1000000, 5000000]  # 0.0001 SOL до 0.005 SOL
            
            for amount in test_amounts:
                logger.info(f"Спроба отримати котирування для {amount/1e9} SOL")
                
                # Спробуємо купити токен
                buy_quote = await self.get_quote(
                    input_mint=WSOL_ADDRESS,
                    amount=amount,
                    output_mint=token_address,
                    slippage=10.0
                )
                
                if buy_quote:
                    logger.info(f"Отримано котирування на купівлю: {buy_quote}")
                    
                    # Спробуємо продати токен
                    sell_quote = await self.get_quote(
                        input_mint=token_address,
                        amount=int(buy_quote['outAmount']),
                        output_mint=WSOL_ADDRESS,
                        slippage=10.0
                    )
                    
                    if sell_quote:
                        logger.info(f"Отримано котирування на продаж: {sell_quote}")
                        
                        # Перевіряємо спред
                        buy_price = float(buy_quote['price'])
                        sell_price = float(sell_quote['price'])
                        spread = abs(buy_price - sell_price) / buy_price
                        
                        logger.info(f"Спред: {spread*100}%")
                        
                        if spread < 0.1:  # Якщо спред менше 10%
                            logger.info(f"Токен має достатню ліквідність (спред {spread*100}%)")
                            return True
                    else:
                        logger.warning(f"Не вдалося отримати котирування на продаж для суми {amount/1e9} SOL")
                else:
                    logger.warning(f"Не вдалося отримати котирування на купівлю для суми {amount/1e9} SOL")
            
            logger.error("Токен не має достатньої ліквідності")
            return False
            
        except Exception as e:
            logger.error(f"Помилка перевірки ліквідності: {str(e)}")
            return False
