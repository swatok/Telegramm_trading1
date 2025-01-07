"""Jupiter DEX client implementation"""

from typing import Dict, Optional
from decimal import Decimal
import aiohttp

class JupiterClient:
    """Клієнт для роботи з Jupiter DEX"""
    
    def __init__(self, api_url: str):
        self._api_url = api_url
        self._session = aiohttp.ClientSession()
        
    async def close(self):
        """Закриття сесії"""
        await self._session.close()
        
    async def get_token_price(self, token_address: str) -> Decimal:
        """Отримання ціни токена"""
        async with self._session.get(f"{self._api_url}/price/{token_address}") as response:
            data = await response.json()
            return Decimal(str(data['price']))
            
    async def get_token_info(self, token_address: str) -> Dict:
        """Отримання інформації про токен"""
        async with self._session.get(f"{self._api_url}/token/{token_address}") as response:
            return await response.json()
            
    async def get_swap_route(self,
                           token_address: str,
                           amount: Decimal,
                           side: str,
                           slippage: Optional[Decimal] = None) -> Dict:
        """Отримання маршруту для свопу"""
        params = {
            'inputMint': 'SOL',
            'outputMint': token_address,
            'amount': str(amount),
            'slippage': str(slippage) if slippage else '1',
            'feeBps': '4'
        }
        
        if side == 'sell':
            params['inputMint'], params['outputMint'] = params['outputMint'], params['inputMint']
            
        async with self._session.get(f"{self._api_url}/quote", params=params) as response:
            return await response.json()
            
    async def create_swap_transaction(self, route: Dict) -> Dict:
        """Створення транзакції для свопу"""
        async with self._session.post(f"{self._api_url}/swap", json=route) as response:
            return await response.json()
            
    async def get_liquidity_pools(self, token_address: str) -> Dict:
        """Отримання інформації про пули ліквідності"""
        async with self._session.get(f"{self._api_url}/pools/{token_address}") as response:
            return await response.json()
            
    async def get_market_depth(self, token_address: str) -> Dict:
        """Отримання глибини ринку"""
        async with self._session.get(f"{self._api_url}/market-depth/{token_address}") as response:
            return await response.json() 