"""Wallet API implementation"""

from typing import Dict, List
from decimal import Decimal

from interfaces.wallet_interface import IWalletAPI
from implementations.solana.wallet import SolanaWallet
from implementations.api.market_api import MarketAPI

class WalletAPI(IWalletAPI):
    """API для взаємодії з гаманцем"""
    
    def __init__(self, wallet: SolanaWallet, market_api: MarketAPI):
        self._wallet = wallet
        self._market_api = market_api
        
    async def get_balance(self, token_address: str = None) -> Decimal:
        """Отримання балансу"""
        if token_address:
            return await self._wallet.get_token_balance(token_address)
        return await self._wallet.get_sol_balance()
        
    async def get_balances(self) -> Dict[str, Decimal]:
        """Отримання всіх балансів"""
        return await self._wallet.get_token_balances()
        
    async def get_portfolio_value(self) -> Dict:
        """Отримання вартості портфеля"""
        balances = await self.get_balances()
        total_value = Decimal('0')
        token_values = {}
        
        for token_address, amount in balances.items():
            if amount > 0:
                price = await self._market_api.get_token_price(token_address)
                value = amount * price
                token_values[token_address] = {
                    'amount': amount,
                    'price': price,
                    'value': value
                }
                total_value += value
                
        return {
            'total_value': total_value,
            'token_values': token_values
        }
        
    async def get_transaction_history(self) -> List[Dict]:
        """Отримання історії транзакцій"""
        return await self._wallet.get_transaction_history()
        
    async def sign_transaction(self, transaction: Dict) -> str:
        """Підписання транзакції"""
        return await self._wallet.sign_transaction(transaction)
        
    async def sign_and_send_transaction(self, transaction: Dict) -> str:
        """Підписання і відправка транзакції"""
        return await self._wallet.sign_and_send_transaction(transaction) 