"""Калькулятор цін"""

from decimal import Decimal
from typing import Dict, Optional, List
from loguru import logger
from api.jupiter import JupiterAPI

class PriceCalculator:
    """Клас для розрахунку цін та розмірів позицій"""
    
    def __init__(self, jupiter_api: JupiterAPI):
        """
        Ініціалізація калькулятора цін
        
        Args:
            jupiter_api: API Jupiter
        """
        self.jupiter = jupiter_api
        
        # Константи
        self.WSOL_ADDRESS = "So11111111111111111111111111111111111111112"
        self.MIN_LIQUIDITY_SOL = Decimal("40")  # Мінімальна ліквідність в SOL
        self.POSITION_SIZE_PERCENT = Decimal("5") / Decimal("100")  # 5% від балансу
        
    async def calculate_position_size(
        self,
        token_address: str,
        balance_sol: Decimal
    ) -> Optional[Dict]:
        """
        Розрахунок розміру позиції
        
        Args:
            token_address: Адреса токену
            balance_sol: Баланс в SOL
            
        Returns:
            Словник з розрахунками або None
        """
        try:
            # Перевіряємо ліквідність
            liquidity = await self.jupiter.get_pool_liquidity(
                token_address,
                self.WSOL_ADDRESS
            )
            
            if not liquidity or liquidity < self.MIN_LIQUIDITY_SOL:
                logger.error(f"Недостатня ліквідність: {liquidity} SOL")
                return None
                
            # Розраховуємо розмір позиції
            position_size_sol = balance_sol * self.POSITION_SIZE_PERCENT
            
            # Отримуємо ціну токена
            price = await self.jupiter.get_price(token_address, self.WSOL_ADDRESS)
            if not price:
                logger.error("Не вдалося отримати ціну")
                return None
                
            # Розраховуємо кількість токенів
            token_amount = position_size_sol / Decimal(str(price))
            
            return {
                'position_size_sol': float(position_size_sol),
                'token_amount': float(token_amount),
                'token_price_sol': float(price),
                'pool_liquidity_sol': float(liquidity)
            }
            
        except Exception as e:
            logger.error(f"Помилка розрахунку розміру позиції: {e}")
            return None
            
    async def calculate_take_profit_levels(
        self,
        entry_price: Decimal,
        levels: List[Dict]
    ) -> List[Dict]:
        """
        Розрахунок рівнів take profit
        
        Args:
            entry_price: Ціна входу
            levels: Список рівнів у форматі [{"level": Decimal, "sell_percent": Decimal}]
            
        Returns:
            Список розрахованих рівнів
        """
        try:
            result = []
            for level in levels:
                price = entry_price * (1 + level['level'])
                result.append({
                    'price': float(price),
                    'percent': float(level['level'] * 100),
                    'sell_percent': float(level['sell_percent'] * 100)
                })
            return result
            
        except Exception as e:
            logger.error(f"Помилка розрахунку take profit: {e}")
            return []
            
    async def calculate_stop_loss(
        self,
        entry_price: Decimal,
        stop_loss_percent: Decimal
    ) -> Optional[float]:
        """
        Розрахунок рівня stop loss
        
        Args:
            entry_price: Ціна входу
            stop_loss_percent: Відсоток stop loss
            
        Returns:
            Ціна stop loss або None
        """
        try:
            stop_loss = entry_price * (1 + stop_loss_percent)
            return float(stop_loss)
            
        except Exception as e:
            logger.error(f"Помилка розрахунку stop loss: {e}")
            return None
