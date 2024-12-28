"""
Модуль для обробки транзакцій
"""

import os
from datetime import datetime
from decimal import Decimal
import asyncio
from loguru import logger
from typing import Optional
from solders.keypair import Keypair
import base58

from api.jupiter import JupiterAPI
from api.quicknode import QuicknodeAPI

# Константи
WSOL_ADDRESS = "So11111111111111111111111111111111111111112"
MIN_SOL_BALANCE = Decimal("0.02")  # Мінімальний баланс SOL для операцій
TRANSACTION_CONFIRMATION_TIMEOUT = 60  # Таймаут очікування підтвердження транзакції в секундах

# Take-profit рівні
TAKE_PROFIT_LEVELS = [
    {"level": Decimal("1"), "sell_percent": Decimal("20")},   # 100% - продаж 20%
    {"level": Decimal("2.5"), "sell_percent": Decimal("20")}, # 250% - продаж 20%
    {"level": Decimal("5"), "sell_percent": Decimal("20")},   # 500% - продаж 20%
    {"level": Decimal("10"), "sell_percent": Decimal("20")},  # 1000% - продаж 20%
    {"level": Decimal("30"), "sell_percent": Decimal("25")},  # 3000% - продаж 25%
    {"level": Decimal("90"), "sell_percent": Decimal("50")}   # 9000% - продаж 50%
]

# Stop-loss рівень
STOP_LOSS_LEVEL = Decimal("-0.75")  # -75%

class TransactionHandler:
    def __init__(self, send_log_callback=None):
        """Ініціалізація обробника транзакцій"""
        self.send_log = send_log_callback or (lambda x: None)
        
        # Ініціалізуємо API клієнти
        self.quicknode = QuicknodeAPI()
        self.jupiter = JupiterAPI()
        
        # Ініціалізуємо keypair
        private_key = os.getenv('SOLANA_PRIVATE_KEY')
        if not private_key:
            raise ValueError("Відсутній SOLANA_PRIVATE_KEY")
        self.keypair = Keypair.from_bytes(base58.b58decode(private_key))
        
    async def wait_for_transaction_confirmation(self, signature: str, max_attempts: int = 30) -> bool:
        """Очікування підтвердження транзакції"""
        attempt = 1
        wait_time = 1  # початковий час очікування в секундах
        
        while attempt <= max_attempts:
            logger.info(f"Спроба {attempt}: Перевірка статусу транзакції {signature}")
            
            status = await self.quicknode.get_transaction_status(signature)
            logger.info(f"Отримано статус: {status}")
            
            if status == 'confirmed':
                # Отримуємо баланс після транзакції
                new_balance = await self.quicknode.get_sol_balance(str(self.keypair.pubkey()))
                logger.info(f"Новий баланс після транзакції: {new_balance:.9f} SOL")
                
                # Відправляємо повідомлення про успішне підтвердження
                await self.send_log(
                    f"✅ Транзакція підтверджена!\n"
                    f"• Підпис: {signature}\n"
                    f"• Посилання: https://solscan.io/tx/{signature}\n"
                    f"• Новий баланс: {new_balance:.9f} SOL"
                )
                return True
                
            elif status == 'failed':
                error_msg = f"❌ Транзакція не вдалася: {signature}"
                logger.error(error_msg)
                await self.send_log(
                    f"{error_msg}\n"
                    f"• Посилання: https://solscan.io/tx/{signature}"
                )
                return False
                
            elif status == 'pending':
                await self.send_log(
                    f"⏳ Очікування підтвердження транзакції...\n"
                    f"• Спроба: {attempt}/{max_attempts}\n"
                    f"• Підпис: {signature}\n"
                    f"• Посилання: https://solscan.io/tx/{signature}"
                )
                
                # Збільшуємо час очікування експоненційно
                logger.info(f"Чекаємо {wait_time} секунд перед наступною спробою...")
                await asyncio.sleep(wait_time)
                wait_time = min(wait_time * 2, 10)  # максимум 10 секунд
                attempt += 1
                continue
                
            else:
                error_msg = f"❌ Помилка перевірки статусу транзакції: {signature}"
                logger.error(error_msg)
                await self.send_log(
                    f"{error_msg}\n"
                    f"• Посилання: https://solscan.io/tx/{signature}"
                )
                return False
        
        error_msg = f"❌ Переви��ено максимальну кількість спроб ({max_attempts}) для транзакції {signature}"
        logger.error(error_msg)
        await self.send_log(
            f"{error_msg}\n"
            f"• Посилання: https://solscan.io/tx/{signature}"
        )
        return False
        
    async def execute_transaction(self, quote_data: dict, reason: str = "") -> Optional[str]:
        """Виконання транзакції"""
        try:
            logger.info(f"Виконуємо транзакцію: {reason}")
            
            signature = await self.jupiter.sign_and_send(quote_data, self.keypair)
            if signature:
                # Чекаємо підтвердження транзакції
                status = await self.wait_for_transaction_confirmation(signature)
                if status == "confirmed":
                    await self.send_log(
                        f"✅ Транзакція виконана успішно:\n"
                        f"• Причина: {reason}\n"
                        f"• Транзакція: https://solscan.io/tx/{signature}"
                    )
                    return signature
                else:
                    await self.send_log(
                        f"❌ Помилк�� виконання транзакції:\n"
                        f"• Причина: {reason}\n"
                        f"• Статус: {status}\n"
                        f"• Транзакція: https://solscan.io/tx/{signature}"
                    )
            return None
                
        except Exception as e:
            logger.error(f"Помилка виконання транзакції: {e}")
            return None
            
    async def execute_swap(self, input_mint: str, output_mint: str, amount: int, slippage: float = 1.0, reason: str = "") -> Optional[str]:
        """Виконання свопу"""
        try:
            logger.info(f"Отримуємо котирування для свопу: {input_mint} -> {output_mint}, сума: {amount}, slippage: {slippage}%")
            
            quote_data = await self.jupiter.get_quote(
                input_mint=input_mint,
                output_mint=output_mint,
                amount=amount,
                slippage=slippage
            )
            
            if not quote_data:
                logger.error("Не вдалося отримати котирування для свопу")
                return None
                
            return await self.execute_transaction(quote_data, reason)
                
        except Exception as e:
            logger.error(f"Помилка виконання свопу: {e}")
            return None 