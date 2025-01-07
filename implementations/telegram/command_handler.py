"""Telegram command handler implementation"""

from typing import Dict, Optional, Tuple
from decimal import Decimal

from interfaces.command_bot_interface import ICommandHandler
from implementations.telegram.bot import TelegramBot

class CommandHandler(ICommandHandler):
    """Імплементація обробника команд"""
    
    def __init__(self):
        self._bot = TelegramBot()
        self._commands = {
            '/buy': self._parse_market_buy,
            '/sell': self._parse_market_sell,
            '/limit_buy': self._parse_limit_buy,
            '/limit_sell': self._parse_limit_sell,
            '/cancel': self._parse_cancel,
            '/orders': self._parse_orders,
            '/info': self._parse_market_info,
            '/alert': self._parse_alert,
            '/help': self._parse_help
        }
    
    async def handle_message(self, user_id: int, message: str) -> str:
        """Обробка повідомлення від користувача"""
        try:
            command, params = self._parse_message(message)
            if command in self._commands:
                parsed_params = self._commands[command](params)
                if parsed_params is None:
                    return self._get_command_help(command)
                return await self._bot.handle_command(user_id, command[1:], parsed_params)
            else:
                return "Невідома команда. Використайте /help для списку команд."
        except Exception as e:
            return f"Помилка обробки команди: {str(e)}"
    
    def _parse_message(self, message: str) -> Tuple[str, str]:
        """Розбір повідомлення на команду та параметри"""
        parts = message.strip().split(' ', 1)
        command = parts[0].lower()
        params = parts[1] if len(parts) > 1 else ''
        return command, params
    
    def _parse_market_buy(self, params: str) -> Optional[Dict]:
        """Розбір параметрів ринкової покупки"""
        parts = params.split()
        if len(parts) < 2:
            return None
            
        return {
            'token': parts[0],
            'amount': parts[1],
            'slippage': parts[2] if len(parts) > 2 else '1.0'
        }
    
    def _parse_market_sell(self, params: str) -> Optional[Dict]:
        """Розбір параметрів ринкового продажу"""
        parts = params.split()
        if len(parts) < 2:
            return None
            
        return {
            'token': parts[0],
            'amount': parts[1],
            'slippage': parts[2] if len(parts) > 2 else '1.0'
        }
    
    def _parse_limit_buy(self, params: str) -> Optional[Dict]:
        """Розбір параметрів лімітної покупки"""
        parts = params.split()
        if len(parts) < 3:
            return None
            
        return {
            'token': parts[0],
            'amount': parts[1],
            'price': parts[2]
        }
    
    def _parse_limit_sell(self, params: str) -> Optional[Dict]:
        """Розбір параметрів лімітного продажу"""
        parts = params.split()
        if len(parts) < 3:
            return None
            
        return {
            'token': parts[0],
            'amount': parts[1],
            'price': parts[2]
        }
    
    def _parse_cancel(self, params: str) -> Optional[Dict]:
        """Розбір параметрів скасування ордеру"""
        if not params:
            return None
            
        return {
            'order_id': params.strip()
        }
    
    def _parse_orders(self, params: str) -> Dict:
        """Розбір параметрів запиту ордерів"""
        return {}
    
    def _parse_market_info(self, params: str) -> Optional[Dict]:
        """Розбір параметрів запиту інформації про ринок"""
        if not params:
            return None
            
        return {
            'token': params.strip()
        }
    
    def _parse_alert(self, params: str) -> Optional[Dict]:
        """Розбір параметрів встановлення алерту"""
        parts = params.split()
        if len(parts) < 2:
            return None
            
        return {
            'token': parts[0],
            'price': parts[1],
            'direction': parts[2] if len(parts) > 2 else 'above'
        }
    
    def _parse_help(self, params: str) -> Dict:
        """Розбір параметрів допомоги"""
        return {}
    
    def _get_command_help(self, command: str) -> str:
        """Отримання довідки по команді"""
        help_texts = {
            '/buy': 'Використання: /buy <токен> <кількість> [макс_проковзування]',
            '/sell': 'Використання: /sell <токен> <кількість> [макс_проковзування]',
            '/limit_buy': 'Використання: /limit_buy <токен> <кількість> <ціна>',
            '/limit_sell': 'Використання: /limit_sell <токен> <кількість> <ціна>',
            '/cancel': 'Використання: /cancel <id_ордеру>',
            '/orders': 'Використання: /orders',
            '/info': 'Використання: /info <токен>',
            '/alert': 'Використання: /alert <токен> <ціна> [above|below]',
            '/help': 'Доступні команди:\n' + '\n'.join(self._commands.keys())
        }
        return help_texts.get(command, 'Невідома команда') 