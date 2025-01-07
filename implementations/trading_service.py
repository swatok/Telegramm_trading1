"""Trading service implementation"""

from typing import Optional, Dict, List
from decimal import Decimal
from datetime import datetime

from interfaces.trading_interface import ITradingService
from implementations.order_manager import OrderManager
from implementations.order_executor import OrderExecutor
from implementations.market_data_provider import MarketDataProvider
from implementations.solana import SolanaImplementation
from implementations.wallet import WalletImplementation
from model.order import Order
from model.position import Position

class TradingService(ITradingService):
    """Імплементація торгового сервісу"""
    
    def __init__(self, 
                 solana: SolanaImplementation,
                 wallet: WalletImplementation,
                 slippage: float = 0.5):
        """
        Ініціалізація торгового сервісу
        
        Args:
            solana: Екземпляр SolanaImplementation
            wallet: Екземпляр WalletImplementation 
            slippage: Допустимий відсоток проковзування (default: 0.5%)
        """
        self._solana = solana
        self._wallet = wallet
        self._slippage = slippage
        self._order_manager = OrderManager()
        self._order_executor = OrderExecutor()
        self._market_data = MarketDataProvider()

    async def create_market_order(self, 
                                token_address: str,
                                amount: Decimal,
                                side: str,
                                max_slippage: Optional[Decimal] = None) -> Order:
        """Створення ринкового ордеру"""
        
        # Перевірка балансу
        if side == 'buy':
            if not await self._wallet.check_sol_balance(amount):
                raise ValueError("Недостатньо SOL для покупки")
        else:
            if not await self._wallet.check_token_balance(token_address, amount):
                raise ValueError("Недостатньо токенів для продажу")
                
        # Отримання ринкових даних
        price = await self._market_data.get_token_price(token_address)
        
        # Створення ордеру
        order = await self._order_manager.create_order(
            token_address=token_address,
            amount=amount,
            price=price,
            side=side,
            order_type='market',
            max_slippage=max_slippage or Decimal(str(self._slippage))
        )
        
        # Виконання ордеру
        executed_order = await self._order_executor.execute_order(order)
        
        # Оновлення позиції
        if executed_order.status == 'filled':
            await self._update_position(executed_order)
            
        return executed_order

    async def create_limit_order(self,
                               token_address: str,
                               amount: Decimal,
                               price: Decimal,
                               side: str) -> Order:
        """Створення лімітного ордеру"""
        
        # Перевірка балансу
        if side == 'buy':
            required_sol = amount * price
            if not await self._wallet.check_sol_balance(required_sol):
                raise ValueError("Недостатньо SOL для покупки")
        else:
            if not await self._wallet.check_token_balance(token_address, amount):
                raise ValueError("Недостатньо токенів для продажу")
                
        # Створення ордеру
        order = await self._order_manager.create_order(
            token_address=token_address,
            amount=amount,
            price=price,
            side=side,
            order_type='limit'
        )
        
        return order

    async def cancel_order(self, order_id: str) -> bool:
        """Скасування ордеру"""
        return await self._order_manager.cancel_order(order_id)

    async def get_active_orders(self) -> List[Order]:
        """Отримання списку активних ордерів"""
        return await self._order_manager.get_active_orders()

    async def get_order_status(self, order_id: str) -> Dict:
        """Отримання статусу ордеру"""
        return await self._order_manager.get_order_status(order_id)

    async def estimate_trade(self,
                           token_address: str,
                           amount: Decimal,
                           side: str) -> Dict:
        """Оцінка торгової операції"""
        price = await self._market_data.get_token_price(token_address)
        gas_cost = await self._solana.estimate_transaction_cost()
        dex_fee = await self._market_data.get_dex_fee(token_address, amount)
        
        return {
            'price': price,
            'total': amount * price,
            'gas_cost': gas_cost,
            'dex_fee': dex_fee
        }

    async def _update_position(self, order: Order) -> None:
        """Оновлення позиції після виконання ордеру"""
        position = Position(
            token_address=order.token_address,
            amount=order.amount,
            entry_price=order.filled_price,
            side=order.side,
            timestamp=datetime.now()
        )
        await self._wallet.update_position(position) 