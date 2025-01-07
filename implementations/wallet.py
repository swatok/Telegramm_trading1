"""Solana wallet implementation"""

from typing import Dict, List
from decimal import Decimal
import base58
from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction
from solana.keypair import Keypair

class SolanaWallet:
    """Клас для роботи з Solana гаманцем"""
    
    def __init__(self, rpc_url: str, private_key: str):
        self._client = AsyncClient(rpc_url)
        self._keypair = Keypair.from_secret_key(base58.b58decode(private_key))
        
    async def close(self):
        """Закриття клієнта"""
        await self._client.close()
        
    async def get_sol_balance(self) -> Decimal:
        """Отримання балансу SOL"""
        response = await self._client.get_balance(self._keypair.public_key)
        return Decimal(response['result']['value']) / Decimal('1000000000')
        
    async def get_token_balance(self, token_address: str) -> Decimal:
        """Отримання балансу токена"""
        response = await self._client.get_token_account_balance(token_address)
        return Decimal(response['result']['value']['uiAmount'])
        
    async def get_token_balances(self) -> Dict[str, Decimal]:
        """Отримання балансів всіх токенів"""
        response = await self._client.get_token_accounts_by_owner(
            self._keypair.public_key,
            {'programId': 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'}
        )
        
        balances = {}
        for account in response['result']['value']:
            mint = account['account']['data']['parsed']['info']['mint']
            amount = Decimal(account['account']['data']['parsed']['info']['tokenAmount']['uiAmount'])
            if amount > 0:
                balances[mint] = amount
                
        return balances
        
    async def get_transaction_history(self) -> List[Dict]:
        """Отримання історії транзакцій"""
        response = await self._client.get_signatures_for_address(self._keypair.public_key)
        
        history = []
        for tx in response['result']:
            tx_info = await self._client.get_transaction(tx['signature'])
            history.append(tx_info['result'])
            
        return history
        
    async def sign_transaction(self, transaction: Dict) -> str:
        """Підписання транзакції"""
        tx = Transaction.deserialize(transaction['data'])
        tx.sign(self._keypair)
        return base58.b58encode(tx.serialize()).decode()
        
    async def sign_and_send_transaction(self, transaction: Dict) -> str:
        """Підписання і відправка транзакції"""
        signed_tx = await self.sign_transaction(transaction)
        response = await self._client.send_raw_transaction(base58.b58decode(signed_tx))
        return response['result'] 