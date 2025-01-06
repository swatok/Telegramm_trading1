"""Виконавець ордерів"""

from decimal import Decimal
from typing import Dict, Optional
from loguru import logger
from api.jupiter import JupiterAPI
from api.quicknode import QuicknodeAPI
from database import TransactionRepository
from model.transaction import Transaction

class OrderExecutor:
    """Клас для виконання торгових ордерів"""
    
    def __init__(
        self,
        jupiter_api: JupiterAPI,
        quicknode_api: QuicknodeAPI,
        transaction_repo: TransactionRepository
    ):
        """
        Ініціалізація виконавця ордерів
        
        Args:
            jupiter_api: API Jupiter
            quicknode_api: API QuickNode
            transaction_repo: Репозиторій транзакцій
        """
        self.jupiter = jupiter_api
        self.quicknode = quicknode_api
        self.transaction_repo = transaction_repo
        
    async def execute_buy(
        self,
        trade_id: int,
        token_address: str,
        amount_in: Decimal,
        slippage: Decimal = Decimal("1.0")
    ) -> Optional[Dict]:
        """
        Виконання ордеру на купівлю
        
        Args:
            trade_id: ID торгу
            token_address: Адреса токену
            amount_in: Кількість SOL для купівлі
            slippage: Допустимий відсоток проковзування
            
        Returns:
            Словник з даними транзакції або None
        """
        try:
            # Отримуємо котирування
            quote = await self.jupiter.get_quote(
                input_mint="So11111111111111111111111111111111111111112",  # WSOL
                output_mint=token_address,
                amount=int(amount_in * Decimal("1000000000")),  # Конвертуємо в lamports
                slippage_bps=int(slippage * 100)  # Конвертуємо в базисні пункти
            )
            
            if not quote:
                logger.error("Не вдалося отримати котирування")
                return None
                
            # Виконуємо своп
            tx_hash = await self.jupiter.swap(quote)
            if not tx_hash:
                logger.error("Не вдалося виконати своп")
                return None
                
            # Чекаємо підтвердження транзакції
            confirmation = await self.quicknode.wait_for_transaction(tx_hash)
            if not confirmation:
                logger.error("Не вдалося отримати підтвердження транзакції")
                return None
                
            # Зберігаємо транзакцію
            transaction = self.transaction_repo.add_transaction(
                trade_id=trade_id,
                tx_hash=tx_hash,
                tx_type='buy',
                amount=float(amount_in),
                price=float(quote.price),
                gas_price=float(confirmation.gas_price),
                gas_used=float(confirmation.gas_used)
            )
            
            if not transaction:
                logger.error("Не вдалося зберегти транзакцію")
                return None
                
            logger.info(f"Виконано купівлю: {tx_hash}")
            return transaction
            
        except Exception as e:
            logger.error(f"Помилка виконання купівлі: {e}")
            return None
            
    async def execute_sell(
        self,
        trade_id: int,
        token_address: str,
        amount_in: Decimal,
        slippage: Decimal = Decimal("1.0")
    ) -> Optional[Dict]:
        """
        Виконання ордеру на продаж
        
        Args:
            trade_id: ID торгу
            token_address: Адреса токену
            amount_in: Кількість токенів для продажу
            slippage: Допустимий відсоток проковзування
            
        Returns:
            Словник з даними транзакції або None
        """
        try:
            # Отримуємо котирування
            quote = await self.jupiter.get_quote(
                input_mint=token_address,
                output_mint="So11111111111111111111111111111111111111112",  # WSOL
                amount=int(amount_in * Decimal("1000000000")),  # Конвертуємо в lamports
                slippage_bps=int(slippage * 100)  # Конвертуємо в базисні пункти
            )
            
            if not quote:
                logger.error("Не вдалося отримати котирування")
                return None
                
            # Виконуємо своп
            tx_hash = await self.jupiter.swap(quote)
            if not tx_hash:
                logger.error("Не вдалося виконати своп")
                return None
                
            # Чекаємо підтвердження транзакції
            confirmation = await self.quicknode.wait_for_transaction(tx_hash)
            if not confirmation:
                logger.error("Не вдалося отримати підтвердження транзакції")
                return None
                
            # Зберігаємо транзакцію
            transaction = self.transaction_repo.add_transaction(
                trade_id=trade_id,
                tx_hash=tx_hash,
                tx_type='sell',
                amount=float(amount_in),
                price=float(quote.price),
                gas_price=float(confirmation.gas_price),
                gas_used=float(confirmation.gas_used)
            )
            
            if not transaction:
                logger.error("Не вдалося зберегти транзакцію")
                return None
                
            logger.info(f"Виконано продаж: {tx_hash}")
            return transaction
            
        except Exception as e:
            logger.error(f"Помилка виконання продажу: {e}")
            return None
