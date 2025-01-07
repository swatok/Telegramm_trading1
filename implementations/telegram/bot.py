"""Telegram bot implementation"""

from typing import Dict, Optional
from decimal import Decimal
from datetime import datetime, timedelta

from interfaces.telegram_interfaces import ITelegramBot
from implementations.trading_service import TradingService
from implementations.monitor_service import MonitorService

class TelegramBot(ITelegramBot):
    """Імплементація Telegram бота"""
    
    def __init__(self):
        self._trading_service = TradingService()
        self._monitor_service = MonitorService()
        self._user_states: Dict[int, Dict] = {}  # user_id -> state
    
    async def handle_command(self, user_id: int, command: str, params: Dict) -> str:
        """Обробка команд від користувача"""
        try:
            if command == 'market_buy':
                return await self._handle_market_buy(user_id, params)
            elif command == 'market_sell':
                return await self._handle_market_sell(user_id, params)
            elif command == 'limit_buy':
                return await self._handle_limit_buy(user_id, params)
            elif command == 'limit_sell':
                return await self._handle_limit_sell(user_id, params)
            elif command == 'cancel_order':
                return await self._handle_cancel_order(user_id, params)
            elif command == 'orders':
                return await self._handle_orders(user_id, params)
            elif command == 'market_info':
                return await self._handle_market_info(user_id, params)
            elif command == 'set_alert':
                return await self._handle_set_alert(user_id, params)
            else:
                return "Невідома команда"
        except Exception as e:
            return f"Помилка: {str(e)}"
    
    async def _handle_market_buy(self, user_id: int, params: Dict) -> str:
        """Обробка ринкової покупки"""
        token_address = params.get('token')
        amount = Decimal(str(params.get('amount')))
        max_slippage = Decimal(str(params.get('slippage', '1.0')))
        
        # Отримуємо оцінку
        estimate = await self._trading_service.estimate_trade(
            token_address=token_address,
            amount=amount,
            side='buy'
        )
        
        # Створюємо ордер
        order = await self._trading_service.create_market_order(
            token_address=token_address,
            amount=amount,
            side='buy',
            max_slippage=max_slippage
        )
        
        if order.status == 'filled':
            return (
                f"✅ Ордер виконано\n"
                f"Ціна: {order.filled_price}\n"
                f"Об'єм: {order.amount}\n"
                f"Комісія: {estimate['gas_cost'] + estimate['dex_fee']}"
            )
        else:
            return f"❌ Помилка виконання ордеру: {order.error}"
    
    async def _handle_market_sell(self, user_id: int, params: Dict) -> str:
        """Обробка ринкового продажу"""
        token_address = params.get('token')
        amount = Decimal(str(params.get('amount')))
        max_slippage = Decimal(str(params.get('slippage', '1.0')))
        
        # Отримуємо оцінку
        estimate = await self._trading_service.estimate_trade(
            token_address=token_address,
            amount=amount,
            side='sell'
        )
        
        # Створюємо ордер
        order = await self._trading_service.create_market_order(
            token_address=token_address,
            amount=amount,
            side='sell',
            max_slippage=max_slippage
        )
        
        if order.status == 'filled':
            return (
                f"✅ Ордер виконано\n"
                f"Ціна: {order.filled_price}\n"
                f"Об'єм: {order.amount}\n"
                f"Комісія: {estimate['gas_cost'] + estimate['dex_fee']}"
            )
        else:
            return f"❌ Помилка виконання ордеру: {order.error}"
    
    async def _handle_limit_buy(self, user_id: int, params: Dict) -> str:
        """Обробка лімітної покупки"""
        token_address = params.get('token')
        amount = Decimal(str(params.get('amount')))
        price = Decimal(str(params.get('price')))
        
        order = await self._trading_service.create_limit_order(
            token_address=token_address,
            amount=amount,
            price=price,
            side='buy'
        )
        
        if order:
            return (
                f"✅ Лімітний ордер створено\n"
                f"Ціна: {order.price}\n"
                f"Об'єм: {order.amount}"
            )
        else:
            return "❌ Помилка створення ордеру"
    
    async def _handle_limit_sell(self, user_id: int, params: Dict) -> str:
        """Обробка лімітного продажу"""
        token_address = params.get('token')
        amount = Decimal(str(params.get('amount')))
        price = Decimal(str(params.get('price')))
        
        order = await self._trading_service.create_limit_order(
            token_address=token_address,
            amount=amount,
            price=price,
            side='sell'
        )
        
        if order:
            return (
                f"✅ Лімітний ордер створено\n"
                f"Ціна: {order.price}\n"
                f"Об'єм: {order.amount}"
            )
        else:
            return "❌ Помилка створення ордеру"
    
    async def _handle_cancel_order(self, user_id: int, params: Dict) -> str:
        """Обробка скасування ордеру"""
        order_id = params.get('order_id')
        
        success = await self._trading_service.cancel_order(order_id)
        if success:
            return "✅ Ордер скасовано"
        else:
            return "❌ Помилка скасування ордеру"
    
    async def _handle_orders(self, user_id: int, params: Dict) -> str:
        """Обробка запиту списку ордерів"""
        active_orders = await self._trading_service.get_active_orders()
        
        if not active_orders:
            return "Немає активних ордерів"
            
        result = "📋 Активні ордери:\n\n"
        for order in active_orders:
            result += (
                f"{'🟢 Купівля' if order.side == 'buy' else '🔴 Продаж'}\n"
                f"Ціна: {order.price}\n"
                f"Об'єм: {order.amount}\n"
                f"Статус: {order.status}\n\n"
            )
        return result
    
    async def _handle_market_info(self, user_id: int, params: Dict) -> str:
        """Обробка запиту інформації про ринок"""
        token_address = params.get('token')
        
        summary = await self._monitor_service.get_market_summary(token_address)
        
        return (
            f"📊 Інформація про ринок:\n\n"
            f"Ціна: {summary['price']}\n"
            f"Зміна: {summary['price_change']}%\n"
            f"Об'єм: {summary['volume']}\n"
            f"Волатильність: {summary['volatility']}%\n"
            f"Ліквідність: {summary['liquidity']}"
        )
    
    async def _handle_set_alert(self, user_id: int, params: Dict) -> str:
        """Обробка встановлення алерту"""
        token_address = params.get('token')
        price = Decimal(str(params.get('price')))
        direction = params.get('direction', 'above')
        
        async def alert_callback(token: str, current_price: Decimal):
            # TODO: Додати відправку повідомлення користувачу через Telegram
            pass
        
        await self._monitor_service.monitor_price(
            token_address=token_address,
            target_price=price,
            direction=direction,
            callback=alert_callback
        )
        
        return (
            f"⚡️ Алерт встановлено\n"
            f"Ціна: {price}\n"
            f"Напрямок: {'вище' if direction == 'above' else 'нижче'}"
        ) 