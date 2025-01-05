"""Менеджер ризиків"""

from decimal import Decimal
from typing import Dict, Optional, List
from loguru import logger
from api.jupiter import JupiterAPI
from api.quicknode import QuicknodeAPI

class RiskManager:
    """Клас для управління торговими ризиками"""
    
    def __init__(
        self,
        jupiter_api: JupiterAPI,
        quicknode_api: QuicknodeAPI,
        min_liquidity_sol: Decimal = Decimal("40"),
        max_slippage_percent: Decimal = Decimal("1"),
        max_position_percent: Decimal = Decimal("5")
    ):
        """
        Ініціалізація менеджера ризиків
        
        Args:
            jupiter_api: API Jupiter
            quicknode_api: API QuickNode
            min_liquidity_sol: Мінімальна ліквідність в SOL
            max_slippage_percent: Максимальне проковзування
            max_position_percent: Максимальний розмір позиції
        """
        self.jupiter = jupiter_api
        self.quicknode = quicknode_api
        self.min_liquidity_sol = min_liquidity_sol
        self.max_slippage_percent = max_slippage_percent
        self.max_position_percent = max_position_percent
        
    async def check_liquidity(
        self,
        token_address: str,
        position_size_sol: Decimal
    ) -> Dict:
        """
        Перевірка ліквідності
        
        Args:
            token_address: Адреса токену
            position_size_sol: Розмір позиції в SOL
            
        Returns:
            Словник з результатами перевірки
        """
        try:
            # Отримуємо ліквідність пулу
            liquidity = await self.jupiter.get_pool_liquidity(
                token_address,
                "So11111111111111111111111111111111111111112"  # WSOL
            )
            
            if not liquidity:
                return {
                    'is_valid': False,
                    'reason': "Не вдалося отримати дані про ліквідність"
                }
                
            # Перевіряємо мінімальну ліквідність
            if liquidity < self.min_liquidity_sol:
                return {
                    'is_valid': False,
                    'reason': f"Недостатня ліквідність: {liquidity} SOL"
                }
                
            # Перевіряємо вплив на ціну
            price_impact = position_size_sol / Decimal(str(liquidity)) * 100
            if price_impact > self.max_slippage_percent:
                return {
                    'is_valid': False,
                    'reason': f"Завеликий вплив на ціну: {price_impact:.2f}%"
                }
                
            return {
                'is_valid': True,
                'liquidity': float(liquidity),
                'price_impact': float(price_impact)
            }
            
        except Exception as e:
            logger.error(f"Помилка перевірки ліквідності: {e}")
            return {
                'is_valid': False,
                'reason': f"Помилка перевірки: {str(e)}"
            }
            
    async def check_token_info(self, token_address: str) -> Dict:
        """
        Перевірка інформації про токен
        
        Args:
            token_address: Адреса токену
            
        Returns:
            Словник з результатами перевірки
        """
        try:
            # Отримуємо інформацію про токен
            token_info = await self.quicknode.get_token_info(token_address)
            if not token_info:
                return {
                    'is_valid': False,
                    'reason': "Не вдалося отримати інформацію про токен"
                }
                
            # Перевіряємо чи токен верифікований
            if not token_info.get('is_verified'):
                return {
                    'is_valid': False,
                    'reason': "Токен не верифікований"
                }
                
            # Перевіряємо чи є холдери
            holders = token_info.get('holder_count', 0)
            if holders < 100:
                return {
                    'is_valid': False,
                    'reason': f"Замало холдерів: {holders}"
                }
                
            return {
                'is_valid': True,
                'token_info': token_info
            }
            
        except Exception as e:
            logger.error(f"Помилка перевірки токена: {e}")
            return {
                'is_valid': False,
                'reason': f"Помилка перевірки: {str(e)}"
            }
            
    async def validate_trade(
        self,
        token_address: str,
        position_size_sol: Decimal,
        balance_sol: Decimal
    ) -> Dict:
        """
        Комплексна перевірка торгівлі
        
        Args:
            token_address: Адреса токену
            position_size_sol: Розмір позиції в SOL
            balance_sol: Баланс в SOL
            
        Returns:
            Словник з результатами перевірки
        """
        # Перевіряємо розмір позиції
        position_percent = position_size_sol / balance_sol * 100
        if position_percent > self.max_position_percent:
            return {
                'is_valid': False,
                'reason': f"Завеликий розмір позиції: {position_percent:.2f}%"
            }
            
        # Перевіряємо ліквідність
        liquidity_check = await self.check_liquidity(token_address, position_size_sol)
        if not liquidity_check['is_valid']:
            return liquidity_check
            
        # Перевіряємо токен
        token_check = await self.check_token_info(token_address)
        if not token_check['is_valid']:
            return token_check
            
        return {
            'is_valid': True,
            'position_percent': float(position_percent),
            'liquidity': liquidity_check.get('liquidity'),
            'price_impact': liquidity_check.get('price_impact'),
            'token_info': token_check.get('token_info')
        }
