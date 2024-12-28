"""Jupiter API wrapper"""

import os
import json
import aiohttp
import ssl
from loguru import logger
from typing import Optional, List, Dict, Any

class JupiterAPI:
    def __init__(self):
        # Список доступних API ендпоінтів
        self.api_endpoints = [
            "https://quote-api.jup.ag/v6",
            "https://price-api.jup.ag/v4",
            "https://token-api.jup.ag"
        ]
        
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
        
    async def _try_endpoints(self, path: str, method: str = "GET", data: dict = None) -> Optional[Dict[str, Any]]:
        """Спроба виконати запит через різні ендпоінти"""
        for endpoint in self.api_endpoints:
            try:
                url = f"{endpoint}/{path}"
                logger.debug(f"Спроба запиту до {url}")
                
                if method == "GET":
                    async with self.session.get(url, headers=self.headers) as response:
                        if response.status == 200:
                            return await response.json()
                elif method == "POST":
                    async with self.session.post(url, headers=self.headers, json=data) as response:
                        if response.status == 200:
                            return await response.json()
                            
            except Exception as e:
                logger.error(f"Помилка запиту до {endpoint}: {str(e)}")
                continue
                
        return None
        
    async def get_token_info(self, mint_address: str) -> Optional[Dict[str, Any]]:
        """Отримання інформації про токен"""
        try:
            # Спроба через різні ендпоінти
            result = await self._try_endpoints("tokens")
            
            if result:
                # Шукаємо токен в списку
                token_info = next(
                    (token for token in result if token.get('address') == mint_address),
                    None
                )
                
                if token_info:
                    logger.info(f"Знайдено інформацію про токен {mint_address}")
                    return token_info
                    
            logger.warning(f"Токен {mint_address} не знайдено в Jupiter API")
            return None
            
        except Exception as e:
            logger.error(f"Помилка отримання інформації про токен: {str(e)}")
            return None
            
    async def get_price(self, input_mint: str, output_mint: str) -> Optional[float]:
        """Отримання ціни токена"""
        try:
            # Спроба через різні ендпоінти
            result = await self._try_endpoints(f"price?ids={input_mint}&vsToken={output_mint}")
            
            if result and "data" in result:
                price_data = result["data"].get(input_mint)
                if price_data:
                    logger.info(f"Отримано ціну для {input_mint}")
                    return float(price_data.get("price", 0))
                    
            logger.warning(f"Не вдалося отримати ціну для {input_mint}")
            return None
            
        except Exception as e:
            logger.error(f"Помилка отримання ціни: {str(e)}")
            return None
            
    async def get_quote(self, input_mint: str, output_mint: str, amount: int, slippage_bps: int = 100) -> Optional[Dict[str, Any]]:
        """Отримання котирування для свопу"""
        try:
            data = {
                "inputMint": input_mint,
                "outputMint": output_mint,
                "amount": str(amount),
                "slippageBps": slippage_bps,
                "onlyDirectRoutes": False,
                "maxAccounts": 15
            }
            
            # Спроба через різні ендпоінти
            result = await self._try_endpoints("quote", method="POST", data=data)
            
            if result:
                logger.info(f"Отримано котирування для {input_mint} -> {output_mint}")
                return result
                
            logger.warning(f"Не вдалося отримати котирування для {input_mint} -> {output_mint}")
            return None
            
        except Exception as e:
            logger.error(f"Помилка отримання котирування: {str(e)}")
            return None
            
    async def get_swap_tx(self, quote: dict, user_public_key: str) -> Optional[Dict[str, Any]]:
        """Отримання транзакції для свопу"""
        try:
            data = {
                "quoteResponse": quote,
                "userPublicKey": user_public_key,
                "wrapUnwrapSOL": True
            }
            
            # Спроба через різні ендпоінти
            result = await self._try_endpoints("swap", method="POST", data=data)
            
            if result:
                logger.info("Отримано транзакцію для свопу")
                return result
                
            logger.warning("Не вдалося отримати транзакцію для свопу")
            return None
            
        except Exception as e:
            logger.error(f"Помилка отримання транзакції: {str(e)}")
            return None