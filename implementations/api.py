from typing import Dict, Any, List, Optional
import aiohttp
import json
from datetime import datetime
from interfaces.api_interface import APIInterface

class APIImplementation(APIInterface):
    """Імплементація для взаємодії з Jupiter API на Solana"""
    
    def __init__(self):
        """Ініціалізація API клієнта"""
        self.base_url = "https://quote-api.jup.ag/v6"
        self.session = None
        self.config = {}
        
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Ініціалізація API з конфігурацією"""
        try:
            self.config = config
            self.session = aiohttp.ClientSession()
            return True
        except Exception as e:
            print(f"Error initializing API: {e}")
            return False
            
    async def get_market_data(self, token_address: str) -> Dict[str, Any]:
        """Отримання ринкових даних для токена"""
        try:
            # Формуємо параметри запиту
            params = {
                "inputMint": token_address,
                "outputMint": "So11111111111111111111111111111111111111112",  # wSOL
                "amount": 1000000  # 1 токен в ламопртах
            }
            
            # Виконуємо запит до Jupiter API
            async with self.session.get(f"{self.base_url}/quote", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'timestamp': datetime.now().isoformat(),
                        'token': token_address,
                        'price': float(data['outAmount']) / 1000000,  # Конвертуємо в SOL
                        'volume': float(data.get('otherAmountThreshold', 0)) / 1000000,
                        'slippage': data.get('priceImpact', 0),
                        'route_info': data.get('routePlan', [])
                    }
                else:
                    print(f"Error getting market data: {response.status}")
                    return {}
                    
        except Exception as e:
            print(f"Error getting market data: {e}")
            return {}
            
    async def place_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Розміщення ордеру через Jupiter API"""
        try:
            # Формуємо параметри транзакції
            transaction_data = {
                "inputMint": order_data['input_token'],
                "outputMint": order_data['output_token'],
                "amount": int(float(order_data['amount']) * 1000000),  # Конвертуємо в ламопрти
                "slippageBps": order_data.get('slippage', 100),  # 1% за замовчуванням
                "feeBps": order_data.get('fee', 0)
            }
            
            # Отримуємо маршрут транзакції
            async with self.session.post(f"{self.base_url}/quote", json=transaction_data) as response:
                if response.status != 200:
                    return {'success': False, 'error': 'Failed to get route'}
                    
                route_data = await response.json()
                
            # Створюємо транзакцію
            transaction_request = {
                "route": route_data,
                "userPublicKey": order_data['wallet_address']
            }
            
            async with self.session.post(f"{self.base_url}/swap", json=transaction_request) as response:
                if response.status == 200:
                    swap_data = await response.json()
                    return {
                        'success': True,
                        'transaction_id': swap_data.get('txid'),
                        'input_amount': float(swap_data.get('inputAmount', 0)) / 1000000,
                        'output_amount': float(swap_data.get('outputAmount', 0)) / 1000000,
                        'timestamp': datetime.now().isoformat()
                    }
                else:
                    return {'success': False, 'error': 'Failed to create swap'}
                    
        except Exception as e:
            print(f"Error placing order: {e}")
            return {'success': False, 'error': str(e)}
            
    async def cancel_order(self, order_id: str) -> bool:
        """Скасування ордеру"""
        # Jupiter не підтримує скасування транзакцій напряму
        # Транзакції або виконуються, або відхиляються
        return False
        
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Отримання статусу ордеру"""
        try:
            # Перевіряємо статус транзакції через RPC
            async with self.session.get(f"{self.config['rpc_url']}", json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTransaction",
                "params": [order_id, {"encoding": "json", "commitment": "confirmed"}]
            }) as response:
                if response.status == 200:
                    data = await response.json()
                    result = data.get('result', {})
                    
                    if result:
                        return {
                            'order_id': order_id,
                            'status': 'completed' if result.get('meta', {}).get('err') is None else 'failed',
                            'timestamp': datetime.now().isoformat(),
                            'details': result
                        }
                    else:
                        return {
                            'order_id': order_id,
                            'status': 'pending',
                            'timestamp': datetime.now().isoformat()
                        }
                else:
                    return {
                        'order_id': order_id,
                        'status': 'unknown',
                        'timestamp': datetime.now().isoformat()
                    }
                    
        except Exception as e:
            print(f"Error getting order status: {e}")
            return {
                'order_id': order_id,
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            
    async def cleanup(self):
        """Очищення ресурсів"""
        if self.session:
            await self.session.close() 