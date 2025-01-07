"""Monitor service implementation"""

from typing import Dict, List, Optional, Callable
from decimal import Decimal
from datetime import datetime

from interfaces.monitor_interface import IMonitorService
from implementations.market_data_provider import MarketDataProvider
from implementations.order_manager import OrderManager
from implementations.wallet import WalletImplementation
from model.alert import Alert
from model.order import Order
from model.position import Position

class MonitorService(IMonitorService):
    """Імплементація сервісу моніторингу"""
    
    def __init__(self,
                 market_data: MarketDataProvider,
                 order_manager: OrderManager,
                 wallet: WalletImplementation):
        self._market_data = market_data
        self._order_manager = order_manager
        self._wallet = wallet
        self._price_alerts: Dict[str, List[Alert]] = {}
        self._volume_alerts: Dict[str, List[Alert]] = {}
        
    async def monitor_price(self,
                          token_address: str,
                          target_price: Decimal,
                          direction: str,
                          callback: Callable) -> None:
        """Моніторинг ціни"""
        alert = Alert(
            token_address=token_address,
            target_value=target_price,
            direction=direction,
            callback=callback,
            created_at=datetime.now()
        )
        
        if token_address not in self._price_alerts:
            self._price_alerts[token_address] = []
            
        self._price_alerts[token_address].append(alert)
        
    async def monitor_volume(self,
                           token_address: str,
                           target_volume: Decimal,
                           direction: str,
                           callback: Callable) -> None:
        """Моніторинг об'єму"""
        alert = Alert(
            token_address=token_address,
            target_value=target_volume,
            direction=direction,
            callback=callback,
            created_at=datetime.now()
        )
        
        if token_address not in self._volume_alerts:
            self._volume_alerts[token_address] = []
            
        self._volume_alerts[token_address].append(alert)
        
    async def check_alerts(self) -> None:
        """Перевірка всіх алертів"""
        # Перевірка цінових алертів
        for token_address, alerts in self._price_alerts.items():
            current_price = await self._market_data.get_token_price(token_address)
            
            for alert in alerts[:]:  # Копіюємо список для безпечного видалення
                if self._check_alert_condition(current_price, alert):
                    await alert.callback(token_address, current_price)
                    alerts.remove(alert)
                    
        # Перевірка об'ємних алертів
        for token_address, alerts in self._volume_alerts.items():
            current_volume = await self._market_data.get_token_volume(token_address)
            
            for alert in alerts[:]:
                if self._check_alert_condition(current_volume, alert):
                    await alert.callback(token_address, current_volume)
                    alerts.remove(alert)
                    
    def _check_alert_condition(self, current_value: Decimal, alert: Alert) -> bool:
        """Перевірка умови алерту"""
        if alert.direction == 'above':
            return current_value >= alert.target_value
        return current_value <= alert.target_value
        
    async def get_market_summary(self, token_address: str) -> Dict:
        """Отримання зведення по ринку"""
        price = await self._market_data.get_token_price(token_address)
        price_change = await self._market_data.get_price_change(token_address)
        volume = await self._market_data.get_token_volume(token_address)
        volatility = await self._market_data.get_volatility(token_address)
        liquidity = await self._market_data.get_liquidity(token_address)
        
        return {
            'price': price,
            'price_change': price_change,
            'volume': volume,
            'volatility': volatility,
            'liquidity': liquidity
        }
        
    async def get_trading_performance(self,
                                    from_time: Optional[datetime] = None,
                                    to_time: Optional[datetime] = None) -> Dict:
        """Отримання статистики торгівлі"""
        # Отримуємо історію ордерів
        filled_orders = await self._order_manager.get_filled_orders(from_time, to_time)
        
        # Розраховуємо статистику
        total_trades = len(filled_orders)
        successful_trades = len([o for o in filled_orders if o.pnl > 0])
        total_profit = sum(o.pnl for o in filled_orders)
        
        # Отримуємо поточні позиції
        positions = await self._wallet.get_positions()
        
        return {
            'total_trades': total_trades,
            'successful_trades': successful_trades,
            'success_rate': successful_trades / total_trades if total_trades > 0 else 0,
            'total_profit': total_profit,
            'open_positions': len(positions),
            'total_value': sum(p.current_value for p in positions)
        }
        
    async def get_position_summary(self, token_address: str) -> Dict:
        """Отримання зведення по позиції"""
        position = await self._wallet.get_position(token_address)
        if not position:
            return None
            
        current_price = await self._market_data.get_token_price(token_address)
        unrealized_pnl = (current_price - position.entry_price) * position.amount
        
        return {
            'entry_price': position.entry_price,
            'current_price': current_price,
            'amount': position.amount,
            'unrealized_pnl': unrealized_pnl,
            'pnl_percentage': (unrealized_pnl / (position.entry_price * position.amount)) * 100
        } 