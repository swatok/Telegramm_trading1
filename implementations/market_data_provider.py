"""Market data provider implementation"""

from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime, timedelta

from interfaces.market_data_interface import IMarketDataProvider
from implementations.api import APIImplementation

class MarketDataProvider(IMarketDataProvider):
    """Імплементація провайдера ринкових даних"""
    
    def __init__(self, api: APIImplementation):
        self._api = api
        self._price_cache: Dict[str, Dict] = {}  # token -> {price, timestamp}
        self._volume_cache: Dict[str, Dict] = {}  # token -> {volume, timestamp}
        self._cache_ttl = timedelta(seconds=10)
        
    async def get_token_price(self, token_address: str) -> Decimal:
        """Отримання поточної ціни токена"""
        # Перевіряємо кеш
        if token_address in self._price_cache:
            cache = self._price_cache[token_address]
            if datetime.now() - cache['timestamp'] < self._cache_ttl:
                return cache['price']
                
        # Отримуємо нові дані
        price = await self._api.get_token_price(token_address)
        
        # Оновлюємо кеш
        self._price_cache[token_address] = {
            'price': price,
            'timestamp': datetime.now()
        }
        
        return price
        
    async def get_token_volume(self, token_address: str) -> Decimal:
        """Отримання об'єму торгів токена"""
        # Перевіряємо кеш
        if token_address in self._volume_cache:
            cache = self._volume_cache[token_address]
            if datetime.now() - cache['timestamp'] < self._cache_ttl:
                return cache['volume']
                
        # Отримуємо нові дані
        volume = await self._api.get_token_volume(token_address)
        
        # Оновлюємо кеш
        self._volume_cache[token_address] = {
            'volume': volume,
            'timestamp': datetime.now()
        }
        
        return volume
        
    async def get_price_change(self, 
                             token_address: str,
                             timeframe: str = '24h') -> Decimal:
        """Отримання зміни ціни"""
        return await self._api.get_price_change(token_address, timeframe)
        
    async def get_volatility(self,
                           token_address: str,
                           timeframe: str = '24h') -> Decimal:
        """Отримання волатильності"""
        prices = await self.get_historical_prices(
            token_address,
            datetime.now() - self._get_timeframe_delta(timeframe),
            datetime.now()
        )
        
        if not prices:
            return Decimal('0')
            
        # Розрахунок волатильності
        price_changes = [
            (prices[i]['price'] - prices[i-1]['price']) / prices[i-1]['price']
            for i in range(1, len(prices))
        ]
        
        if not price_changes:
            return Decimal('0')
            
        mean = sum(price_changes) / len(price_changes)
        variance = sum((x - mean) ** 2 for x in price_changes) / len(price_changes)
        return Decimal(str(variance ** 0.5 * 100))
        
    async def get_liquidity(self, token_address: str) -> Decimal:
        """Отримання ліквідності"""
        return await self._api.get_token_liquidity(token_address)
        
    async def get_historical_prices(self,
                                  token_address: str,
                                  from_time: datetime,
                                  to_time: datetime) -> List[Dict]:
        """Отримання історичних цін"""
        return await self._api.get_historical_prices(
            token_address,
            from_time,
            to_time
        )
        
    async def get_market_depth(self,
                             token_address: str,
                             depth: int = 10) -> Dict[str, List[Dict]]:
        """Отримання глибини ринку"""
        return await self._api.get_market_depth(token_address, depth)
        
    async def get_dex_fee(self,
                         token_address: str,
                         amount: Decimal) -> Decimal:
        """Отримання комісії DEX"""
        return await self._api.get_dex_fee(token_address, amount)
        
    def _get_timeframe_delta(self, timeframe: str) -> timedelta:
        """Конвертація часового проміжку в timedelta"""
        if timeframe == '1h':
            return timedelta(hours=1)
        elif timeframe == '4h':
            return timedelta(hours=4)
        elif timeframe == '12h':
            return timedelta(hours=12)
        elif timeframe == '24h':
            return timedelta(days=1)
        elif timeframe == '7d':
            return timedelta(days=7)
        elif timeframe == '30d':
            return timedelta(days=30)
        else:
            raise ValueError(f"Невідомий часовий проміжок: {timeframe}") 