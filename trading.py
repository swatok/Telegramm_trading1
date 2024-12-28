"""Trading executor"""

import os
import json
import asyncio
import base58
from loguru import logger
from decimal import Decimal
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from typing import Optional, Dict, Any

from api.quicknode import QuicknodeAPI
from api.jupiter import JupiterAPI
from models.signal import Signal
from models.trade import Trade
from models.token import Token
from monitoring.monitor import Monitor

class TradingExecutor:
    def __init__(self, monitor: Monitor):
        self.monitor = monitor
        self.quicknode = QuicknodeAPI()
        self.jupiter = JupiterAPI()
        self.running = False
        
        # Завантажуємо keypair
        private_key = os.getenv('SOLANA_PRIVATE_KEY')
        if not private_key:
            raise ValueError("SOLANA_PRIVATE_KEY не знайдено в змінних середовища")
            
        self.keypair = Keypair.from_base58_string(private_key)
        self.public_key = str(self.keypair.pubkey())
        
        # Налаштування для торгівлі
        self.WSOL_ADDRESS = "So11111111111111111111111111111111111111112"
        self.MIN_SOL_BALANCE = 0.05
        self.SLIPPAGE_BPS = 100
        
    async def start(self):
        """Запуск торгового виконавця"""
        self.running = True
        logger.info("Торговий виконавець запущено")
        
    async def stop(self):
        """Зупинка торгового виконавця"""
        self.running = False
        await self.quicknode.close()
        await self.jupiter.close()
        logger.info("Торговий виконавець зупинено")
        
    async def verify_token(self, token_address: str) -> bool:
        """Перевірка існування токена"""
        try:
            # Спочатку перевіряємо через Jupiter API
            token_info = await self.jupiter.get_token_info(token_address)
            if token_info:
                logger.info(f"Токен {token_address} знайдено в Jupiter API")
                return True
                
            # Якщо не знайдено в Jupiter, перевіряємо через Solana
            exists = await self.quicknode.verify_token(token_address)
            if exists:
                logger.info(f"Токен {token_address} знайдено в Solana")
                return True
                
            logger.warning(f"Токен {token_address} не знайдено")
            return False
            
        except Exception as e:
            logger.error(f"Помилка перевірки токена: {str(e)}")
            return False
            
    async def get_token_info(self, token_address: str) -> Optional[Dict[str, Any]]:
        """Отримання інформації про токен"""
        try:
            # Спочатку пробуємо через Jupiter API
            token_info = await self.jupiter.get_token_info(token_address)
            if token_info:
                logger.info(f"Отримано інформацію про токен {token_address} з Jupiter API")
                return token_info
                
            # Якщо не знайдено в Jupiter, пробуємо через Solana
            token_info = await self.quicknode.get_token_info(token_address)
            if token_info:
                logger.info(f"Отримано інформацію про токен {token_address} з Solana")
                return token_info
                
            logger.warning(f"Не вдалося отримати інформацію про токен {token_address}")
            return None
            
        except Exception as e:
            logger.error(f"Помилка отримання інформації про токен: {str(e)}")
            return None
            
    async def get_balance(self, token_address: str = None) -> float:
        """Отримання балансу токена"""
        try:
            if not token_address or token_address == self.WSOL_ADDRESS:
                return await self.quicknode.get_sol_balance(self.public_key)
            else:
                return await self.quicknode.get_token_balance(token_address, self.public_key)
                
        except Exception as e:
            logger.error(f"Помилка отримання балансу: {str(e)}")
            return 0.0
            
    async def handle_trade_signal(self, signal: Signal):
        """Обробка торгового сигналу"""
        try:
            if not self.running:
                logger.warning("Торговий виконавець не запущено")
                return
                
            logger.info(f"Обробка сигналу: {signal}")
            
            # Перевіряємо існування токена
            if not await self.verify_token(signal.token_address):
                logger.error(f"Токен {signal.token_address} не існує")
                return
                
            # Отримуємо інформацію про токен
            token_info = await self.get_token_info(signal.token_address)
            if not token_info:
                logger.error(f"Не вдалося отримати інформацію про токен {signal.token_address}")
                return
                
            # Перевіряємо баланс SOL
            sol_balance = await self.get_balance()
            if sol_balance < self.MIN_SOL_BALANCE:
                logger.error(f"Недостатньо SOL для торгівлі: {sol_balance}")
                return
                
            # Отримуємо тестове котирування
            test_amount = 1000000  # 0.001 SOL
            test_quote = await self.jupiter.get_quote(
                self.WSOL_ADDRESS,
                signal.token_address,
                test_amount,
                self.SLIPPAGE_BPS
            )
            
            if not test_quote:
                logger.error("Не вдалося отримати тестове котирування")
                return
                
            # Розраховуємо суму для торгівлі
            trade_amount = int(sol_balance * 0.9 * 1e9)  # 90% від балансу в лампортах
            
            # Отримуємо реальне котирування
            quote = await self.jupiter.get_quote(
                self.WSOL_ADDRESS,
                signal.token_address,
                trade_amount,
                self.SLIPPAGE_BPS
            )
            
            if not quote:
                logger.error("Не вдалося отримати котирування для торгівлі")
                return
                
            # Отримуємо транзакцію
            swap_tx = await self.jupiter.get_swap_tx(quote, self.public_key)
            if not swap_tx:
                logger.error("Не вдалося отримати транзакцію для свопу")
                return
                
            # Зберігаємо торгівлю в базі даних
            trade = Trade(
                token_address=signal.token_address,
                amount=trade_amount,
                quote=quote,
                status="pending"
            )
            await self.monitor.save_trade(trade)
            
            # Відправляємо транзакцію
            signature = await self.sign_and_send_transaction(swap_tx)
            if not signature:
                logger.error("Не вдалося відправити транзакцію")
                trade.status = "failed"
                await self.monitor.update_trade(trade)
                return
                
            # Оновлюємо статус торгівлі
            trade.signature = signature
            trade.status = "sent"
            await self.monitor.update_trade(trade)
            
            # Чекаємо підтвердження транзакції
            confirmed = await self.wait_for_confirmation(signature)
            if confirmed:
                trade.status = "completed"
            else:
                trade.status = "failed"
                
            await self.monitor.update_trade(trade)
            
        except Exception as e:
            logger.error(f"Помилка обробки сигналу: {str(e)}")
            
    async def sign_and_send_transaction(self, swap_tx: Dict[str, Any]) -> Optional[str]:
        """Підписання та відправка транзакції"""
        try:
            # Отримуємо транзакцію в base64
            tx_data = swap_tx.get('swapTransaction')
            if not tx_data:
                logger.error("Не знайдено транзакцію в відповіді")
                return None
                
            # Декодуємо та підписуємо транзакцію
            tx_bytes = base58.b58decode(tx_data)
            signature = self.keypair.sign_message(tx_bytes)
            
            # Відправляємо підписану транзакцію
            response = await self.quicknode._make_request(
                "sendTransaction",
                [
                    base58.b58encode(signature).decode(),
                    {"encoding": "base58", "skipPreflight": True}
                ]
            )
            
            if response:
                logger.info(f"Транзакцію відправлено: {response}")
                return response
                
            logger.error("Не вдалося відправити транзакцію")
            return None
            
        except Exception as e:
            logger.error(f"Помилка підписання/відправки транзакції: {str(e)}")
            return None
            
    async def wait_for_confirmation(self, signature: str, timeout: int = 60) -> bool:
        """Очікування підтвердження транзакції"""
        try:
            start_time = asyncio.get_event_loop().time()
            while True:
                status = await self.quicknode.get_transaction_status(signature)
                
                if status == "confirmed":
                    logger.info(f"Транзакцію {signature} підтверджено")
                    return True
                elif status == "failed":
                    logger.error(f"Транзакцію {signature} відхилено")
                    return False
                    
                if asyncio.get_event_loop().time() - start_time > timeout:
                    logger.error(f"Таймаут очікування підтвердження транзакції {signature}")
                    return False
                    
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Помилка очікування підтвердження: {str(e)}")
            return False