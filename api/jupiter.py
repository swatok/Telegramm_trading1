"""Jupiter API wrapper"""

import os
import json
import aiohttp
from loguru import logger
from solders.keypair import Keypair
from decimal import Decimal
from typing import Optional, Dict
import base64
from base58 import b58decode
from solana.transaction import Transaction
from solders.instruction import Instruction as TransactionInstruction
from solders.hash import Hash
from solders.pubkey import Pubkey
from solders.signature import Signature
import asyncio
from solana.rpc.types import TxOpts
from solana.rpc.api import Client

class JupiterAPI:
    def __init__(self):
        self.endpoint = os.getenv('JUPITER_API_URL')
        if not self.endpoint:
            raise ValueError("JUPITER_API_URL не знайдено в змінних середовища")
            
        self.session = aiohttp.ClientSession()
        self.connection = Client(os.getenv('QUICKNODE_HTTP_URL'))
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
            
    async def get_quote(self, input_mint: str, output_mint: str, amount: int,
                       slippage_bps: Optional[int] = None) -> Dict:
        """Отримання котирування від Jupiter"""
        if slippage_bps is None:
            slippage_bps = 100
            
        url = f"{self.endpoint}/quote"
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": str(amount),  # Вже в лампортах
            "slippageBps": slippage_bps,
            "asLegacyTransaction": "true"
        }
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Помилка отримання котирування: {error_text}")
                    return None
                    
                data = await response.json()
                logger.info(f"Отримано котирування: {json.dumps(data, indent=2)}")
                return data
        except Exception as e:
            logger.error(f"Помилка запиту котирування: {str(e)}")
            return None
            
    async def get_swap_transaction(self, quote_response: Dict, user_public_key: str) -> Dict:
        """Отримання транзакції свопу"""
        url = f"{self.endpoint}/swap"
        
        # Формуємо тіло запиту згідно з документацією Jupiter API v6
        body = {
            "quoteResponse": quote_response,
            "userPublicKey": user_public_key,
            "wrapAndUnwrapSol": True,
            "useSharedAccounts": True,
            "feeAccount": None,
            "computeUnitPriceMicroLamports": 500000,
            "asLegacyTransaction": True
        }
        
        try:
            async with self.session.post(url, json=body) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Помилка отримання транзакції: {error_text}")
                    return None
                    
                data = await response.json()
                logger.info(f"Отримано транзакцію: {json.dumps(data, indent=2)}")
                return data
        except Exception as e:
            logger.error(f"Помилка запиту транзакції: {str(e)}")
            return None
            
    async def sign_and_send(self, quote_response: Dict, keypair: Keypair) -> Optional[str]:
        """Підписання та відправка транзакції"""
        try:
            # Отримуємо транзакцію
            swap_transaction = await self.get_swap_transaction(
                quote_response,
                str(keypair.pubkey())
            )
            
            if not swap_transaction or 'swapTransaction' not in swap_transaction:
                logger.error("Не вдалося отримати транзакцію свопу")
                return None
                
            # Декодуємо транзакцію
            transaction = Transaction.deserialize(
                base64.b64decode(swap_transaction['swapTransaction'])
            )
            
            # Отримуємо останній блокхеш
            blockhash = self.connection.get_latest_blockhash()
            transaction.recent_blockhash = blockhash.value.blockhash
            
            # Підписуємо транзакцію
            transaction.sign(keypair)
            
            # Відправляємо транзакцію
            opts = TxOpts(
                skip_preflight=True,
                preflight_commitment="processed",
                max_retries=3
            )
            
            signature = self.connection.send_transaction(
                transaction,
                keypair,
                opts=opts
            )
            
            logger.info(f"Транзакцію відправлено: {signature.value}")
            return signature.value
            
        except Exception as e:
            logger.error(f"Помилка підписання/відправки транзакції: {str(e)}")
            return None
            
    async def close(self):
        """Закриття сесії"""
        if not self.session.closed:
            await self.session.close()