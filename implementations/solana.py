from typing import Dict, Any, Optional, List
import aiohttp
import json
from datetime import datetime
from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction
from solana.system_program import TransferParams, transfer
from interfaces.solana_interface import SolanaInterface

class SolanaImplementation(SolanaInterface):
    """Імплементація для взаємодії з мережею Solana"""
    
    def __init__(self):
        """Ініціалізація Solana клієнта"""
        self.config = {}
        self.client = None
        self.session = None
        self.jupiter_session = None
        
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Ініціалізація з конфігурацією"""
        try:
            self.config = config
            
            # Ініціалізуємо RPC клієнт
            self.client = AsyncClient(config['rpc_url'])
            
            # Створюємо сесії для API запитів
            self.session = aiohttp.ClientSession()
            self.jupiter_session = aiohttp.ClientSession(
                base_url="https://quote-api.jup.ag/v6"
            )
            
            return True
            
        except Exception as e:
            print(f"Error initializing Solana client: {e}")
            return False
            
    async def connect_to_network(self) -> bool:
        """Підключення до мережі"""
        try:
            # Перевіряємо підключення
            response = await self.client.get_health()
            return response['result'] == "ok"
            
        except Exception as e:
            print(f"Error connecting to Solana network: {e}")
            return False
            
    async def get_contract_info(self, contract_address: str) -> Dict[str, Any]:
        """Отримання інформації про контракт"""
        try:
            # Отримуємо інформацію про аккаунт
            response = await self.client.get_account_info(contract_address)
            
            if 'result' not in response:
                return {}
                
            account_info = response['result']
            if not account_info:
                return {}
                
            return {
                'address': contract_address,
                'owner': account_info['owner'],
                'lamports': account_info['lamports'],
                'data': account_info['data'],
                'executable': account_info['executable']
            }
            
        except Exception as e:
            print(f"Error getting contract info: {e}")
            return {}
            
    async def check_liquidity(self, token_address: str) -> Dict[str, Any]:
        """Перевірка ліквідності токена"""
        try:
            # Отримуємо котирування через Jupiter
            params = {
                "inputMint": token_address,
                "outputMint": "So11111111111111111111111111111111111111112",  # wSOL
                "amount": 1000000  # 1 токен
            }
            
            async with self.jupiter_session.get("/quote", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'token': token_address,
                        'price': float(data['outAmount']) / 1000000,
                        'liquidity': float(data.get('inAmount', 0)) / 1000000,
                        'slippage': data.get('priceImpact', 0),
                        'timestamp': datetime.now().isoformat()
                    }
                return {}
                
        except Exception as e:
            print(f"Error checking liquidity: {e}")
            return {}
            
    async def execute_swap(self, swap_data: Dict[str, Any]) -> Dict[str, Any]:
        """Виконання свопу"""
        try:
            # Формуємо параметри транзакції
            transaction_data = {
                "inputMint": swap_data['input_token'],
                "outputMint": swap_data['output_token'],
                "amount": int(float(swap_data['amount']) * 1000000),
                "slippageBps": swap_data.get('slippage', 100),
                "feeBps": swap_data.get('fee', 0)
            }
            
            # Отримуємо маршрут транзакції
            async with self.jupiter_session.post("/quote", json=transaction_data) as response:
                if response.status != 200:
                    return {'success': False, 'error': 'Failed to get route'}
                    
                route_data = await response.json()
                
            # Створюємо транзакцію
            transaction_request = {
                "route": route_data,
                "userPublicKey": swap_data['wallet_address']
            }
            
            async with self.jupiter_session.post("/swap", json=transaction_request) as response:
                if response.status == 200:
                    swap_response = await response.json()
                    return {
                        'success': True,
                        'transaction_id': swap_response.get('txid'),
                        'input_amount': float(swap_response.get('inputAmount', 0)) / 1000000,
                        'output_amount': float(swap_response.get('outputAmount', 0)) / 1000000,
                        'timestamp': datetime.now().isoformat()
                    }
                else:
                    return {'success': False, 'error': 'Failed to create swap'}
                    
        except Exception as e:
            print(f"Error executing swap: {e}")
            return {'success': False, 'error': str(e)}
            
    async def get_token_balance(self, token_address: str, wallet_address: str) -> Dict[str, Any]:
        """Отримання балансу токена"""
        try:
            # Отримуємо інформацію про токен аккаунт
            response = await self.client.get_token_accounts_by_owner(
                wallet_address,
                {'mint': token_address}
            )
            
            if 'result' not in response:
                return {'balance': 0}
                
            accounts = response['result']['value']
            if not accounts:
                return {'balance': 0}
                
            # Сумуємо баланси всіх аккаунтів
            total_balance = sum(
                int(account['account']['data']['parsed']['info']['tokenAmount']['amount'])
                for account in accounts
            )
            
            return {
                'token': token_address,
                'wallet': wallet_address,
                'balance': total_balance / 1000000,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error getting token balance: {e}")
            return {'balance': 0}
            
    async def get_transaction_status(self, transaction_id: str) -> Dict[str, Any]:
        """Отримання статусу транзакції"""
        try:
            response = await self.client.get_transaction(
                transaction_id,
                encoding="jsonParsed"
            )
            
            if 'result' not in response:
                return {'status': 'unknown'}
                
            result = response['result']
            if not result:
                return {'status': 'pending'}
                
            return {
                'transaction_id': transaction_id,
                'status': 'completed' if result.get('meta', {}).get('err') is None else 'failed',
                'timestamp': datetime.now().isoformat(),
                'block_time': result.get('blockTime'),
                'fee': result.get('meta', {}).get('fee', 0),
                'logs': result.get('meta', {}).get('logMessages', [])
            }
            
        except Exception as e:
            print(f"Error getting transaction status: {e}")
            return {'status': 'error', 'error': str(e)}
            
    async def cleanup(self) -> None:
        """Очищення ресурсів"""
        try:
            if self.client:
                await self.client.close()
            if self.session:
                await self.session.close()
            if self.jupiter_session:
                await self.jupiter_session.close()
        except Exception as e:
            print(f"Error cleaning up Solana client: {e}") 