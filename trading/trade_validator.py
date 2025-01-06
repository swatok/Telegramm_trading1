"""Валідатор торгів"""

from decimal import Decimal
from typing import Dict, Optional
from loguru import logger
from api.jupiter import JupiterAPI
from api.quicknode import QuicknodeAPI

class TradeValidator:
    """Клас для валідації торгових операцій"""
    
    def __init__(
        self,
        jupiter_api: JupiterAPI,
        quicknode_api: QuicknodeAPI,
        min_trade_size_sol: Decimal = Decimal("0.001"),
        min_sol_balance: Decimal = Decimal("0.02")
    ):
        """
        Ініціалізація валідатора торгів
        
        Args:
            jupiter_api: API Jupiter
            quicknode_api: API QuickNode
            min_trade_size_sol: Мінімальний розмір торгу в SOL
            min_sol_balance: Мінімальний баланс SOL
        """
        self.jupiter = jupiter_api
        self.quicknode = quicknode_api
        self.min_trade_size_sol = min_trade_size_sol
        self.min_sol_balance = min_sol_balance
        
    async def validate_buy(
        self,
        token_address: str,
        amount_in_sol: Decimal,
        balance_sol: Decimal
    ) -> Dict:
        """
        Валідація купівлі
        
        Args:
            token_address: Адреса токену
            amount_in_sol: Кількість SOL для купівлі
            balance_sol: Поточний баланс SOL
            
        Returns:
            Словник з результатами валідації
        """
        try:
            # Перевіряємо мінімальний розмір торгу
            if amount_in_sol < self.min_trade_size_sol:
                return {
                    'is_valid': False,
                    'reason': f"Замалий розмір торгу: {amount_in_sol} SOL"
                }
                
            # Перевіряємо достатність балансу
            if balance_sol < (amount_in_sol + self.min_sol_balance):
                return {
                    'is_valid': False,
                    'reason': f"Недостатньо SOL: {balance_sol}"
                }
                
            # Перевіряємо чи існує токен
            token_info = await self.quicknode.get_token_info(token_address)
            if not token_info:
                return {
                    'is_valid': False,
                    'reason': "Токен не знайдено"
                }
                
            # Перевіряємо чи можна торгувати
            quote = await self.jupiter.get_quote(
                input_mint="So11111111111111111111111111111111111111112",  # WSOL
                output_mint=token_address,
                amount=int(amount_in_sol * Decimal("1000000000"))  # Конвертуємо в lamports
            )
            
            if not quote:
                return {
                    'is_valid': False,
                    'reason': "Не вдалося отримати котирування"
                }
                
            return {
                'is_valid': True,
                'quote': quote
            }
            
        except Exception as e:
            logger.error(f"Помилка валідації купівлі: {e}")
            return {
                'is_valid': False,
                'reason': f"Помилка валідації: {str(e)}"
            }
            
    async def validate_sell(
        self,
        token_address: str,
        token_amount: Decimal,
        token_balance: Decimal
    ) -> Dict:
        """
        Валідація продажу
        
        Args:
            token_address: Адреса токену
            token_amount: Кількість токенів для продажу
            token_balance: Поточний баланс токенів
            
        Returns:
            Словник з результатами валідації
        """
        try:
            # Перевіряємо достатність балансу
            if token_balance < token_amount:
                return {
                    'is_valid': False,
                    'reason': f"Недостатньо токенів: {token_balance}"
                }
                
            # Отримуємо ціну в SOL
            price = await self.jupiter.get_price(token_address, "So11111111111111111111111111111111111111112")
            if not price:
                return {
                    'is_valid': False,
                    'reason': "Не вдалося отримати ціну"
                }
                
            # Перевіряємо мінімальний розмір торгу
            amount_in_sol = token_amount * Decimal(str(price))
            if amount_in_sol < self.min_trade_size_sol:
                return {
                    'is_valid': False,
                    'reason': f"Замалий розмір торгу: {amount_in_sol} SOL"
                }
                
            # Перевіряємо чи можна торгувати
            quote = await self.jupiter.get_quote(
                input_mint=token_address,
                output_mint="So11111111111111111111111111111111111111112",  # WSOL
                amount=int(token_amount * Decimal("1000000000"))  # Конвертуємо в lamports
            )
            
            if not quote:
                return {
                    'is_valid': False,
                    'reason': "Не вдалося отримати котирування"
                }
                
            return {
                'is_valid': True,
                'quote': quote,
                'amount_in_sol': float(amount_in_sol)
            }
            
        except Exception as e:
            logger.error(f"Помилка валідації продажу: {e}")
            return {
                'is_valid': False,
                'reason': f"Помилка валідації: {str(e)}"
            }
            
    async def validate_token(self, token_address: str) -> Dict:
        """
        Валідація токену
        
        Args:
            token_address: Адреса токену
            
        Returns:
            Словник з результатами валідації
        """
        try:
            # Перевіряємо чи існує токен
            token_info = await self.quicknode.get_token_info(token_address)
            if not token_info:
                return {
                    'is_valid': False,
                    'reason': "Токен не знайдено"
                }
                
            # Перевіряємо чи можна торгувати через Jupiter
            price = await self.jupiter.get_price(token_address, "So11111111111111111111111111111111111111112")
            if not price:
                return {
                    'is_valid': False,
                    'reason': "Токен недоступний для торгівлі"
                }
                
            return {
                'is_valid': True,
                'token_info': token_info,
                'price_sol': float(price)
            }
            
        except Exception as e:
            logger.error(f"Помилка валідації токену: {e}")
            return {
                'is_valid': False,
                'reason': f"Помилка валідації: {str(e)}"
            }
