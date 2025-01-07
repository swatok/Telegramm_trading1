"""DEX API implementation"""

from typing import Dict, Optional
from decimal import Decimal

from interfaces.dex_interface import IDexAPI
from implementations.solana.wallet import SolanaWallet
from implementations.jupiter.client import JupiterClient

class DexAPI(IDexAPI):
    """API для взаємодії з DEX"""
    
    def __init__(self, wallet: SolanaWallet, jupiter_client: JupiterClient):
        self._wallet = wallet
        self._jupiter = jupiter_client
        
    async def get_token_price(self, token_address: str) -> Decimal:
        """Отримання ціни токена"""
        return await self._jupiter.get_token_price(token_address)
        
    async def get_token_info(self, token_address: str) -> Dict:
        """Отримання інформації про токен"""
        return await self._jupiter.get_token_info(token_address)
        
    async def execute_swap(self,
                         token_address: str,
                         amount: Decimal,
                         side: str,
                         price: Optional[Decimal] = None,
                         slippage: Optional[Decimal] = None) -> Dict:
        """Виконання свопу"""
        try:
            # Отримуємо маршрут для свопу
            route = await self._jupiter.get_swap_route(
                token_address=token_address,
                amount=amount,
                side=side,
                slippage=slippage
            )
            
            if not route:
                return {
                    'success': False,
                    'error': 'No route found'
                }
                
            # Перевіряємо ціну
            if price and abs(route['price'] - price) / price > 0.01:
                return {
                    'success': False, 
                    'error': 'Price impact too high'
                }
                
            # Виконуємо своп
            transaction = await self._jupiter.create_swap_transaction(route)
            
            # Підписуємо і відправляємо транзакцію
            signature = await self._wallet.sign_and_send_transaction(transaction)
            
            return {
                'success': True,
                'transaction_hash': signature,
                'price': route['price'],
                'amount': amount
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
            
    async def get_liquidity_pools(self, token_address: str) -> Dict:
        """Отримання інформації про пули ліквідності"""
        return await self._jupiter.get_liquidity_pools(token_address)
        
    async def get_market_depth(self, token_address: str) -> Dict:
        """Отримання глибини ринку"""
        return await self._jupiter.get_market_depth(token_address) 