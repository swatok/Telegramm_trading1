from typing import Dict, Any, Callable, List, Optional
from interfaces import CommandBotInterface
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes

class CommandHandler(CommandBotInterface):
    """Реалізація інтерфейсу для бота керування"""

    def __init__(self):
        self.commands = {}
        self.admin_commands = set()
        self.admin_users = set()

    async def register_command(self, 
                             command: str, 
                             handler: Callable,
                             description: str) -> bool:
        """Реєстрація нової команди"""
        try:
            self.commands[command] = {
                "handler": handler,
                "description": description
            }
            return True
        except Exception as e:
            print(f"Помилка реєстрації команди: {e}")
            return False

    async def process_command(self, 
                            command: str, 
                            args: List[str],
                            user_id: int) -> Dict[str, Any]:
        """Обробка отриманої команди"""
        try:
            if not await self.check_permissions(user_id, command):
                return {"success": False, "message": "Недостатньо прав"}

            if command not in self.commands:
                return {"success": False, "message": "Команда не знайдена"}

            handler = self.commands[command]["handler"]
            result = await handler(args)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "message": str(e)}

    async def check_permissions(self, user_id: int, command: str) -> bool:
        """Перевірка прав користувача"""
        if command in self.admin_commands:
            return user_id in self.admin_users
        return True

    async def send_response(self, 
                          user_id: int, 
                          message: str,
                          keyboard: Optional[Dict[str, Any]] = None) -> bool:
        """Відправка відповіді користувачу"""
        try:
            # Тут буде логіка відправки повідомлення через Telegram API
            markup = None
            if keyboard:
                markup = InlineKeyboardMarkup(keyboard)
            
            # Відправка повідомлення
            return True
        except Exception as e:
            print(f"Помилка відправки відповіді: {e}")
            return False

    def add_admin(self, user_id: int) -> None:
        """Додавання адміністратора"""
        self.admin_users.add(user_id)

    def add_admin_command(self, command: str) -> None:
        """Позначення команди як адміністраторської"""
        self.admin_commands.add(command) 