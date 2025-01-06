from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, List, Optional

class CommandBotInterface(ABC):
    """Інтерфейс для бота керування"""

    @abstractmethod
    async def register_command(self, 
                             command: str, 
                             handler: Callable,
                             description: str) -> bool:
        """
        Реєстрація нової команди

        Args:
            command: Назва команди
            handler: Функція-обробник команди
            description: Опис команди

        Returns:
            True якщо команда зареєстрована успішно, False інакше
        """
        pass

    @abstractmethod
    async def process_command(self, 
                            command: str, 
                            args: List[str],
                            user_id: int) -> Dict[str, Any]:
        """
        Обробка отриманої команди

        Args:
            command: Назва команди
            args: Аргументи команди
            user_id: ID користувача

        Returns:
            Результат виконання команди
        """
        pass

    @abstractmethod
    async def check_permissions(self, user_id: int, command: str) -> bool:
        """
        Перевірка прав користувача на виконання команди

        Args:
            user_id: ID користувача
            command: Назва команди

        Returns:
            True якщо користувач має права, False інакше
        """
        pass

    @abstractmethod
    async def send_response(self, 
                          user_id: int, 
                          message: str,
                          keyboard: Optional[Dict[str, Any]] = None) -> bool:
        """
        Відправка відповіді користувачу

        Args:
            user_id: ID користувача
            message: Текст повідомлення
            keyboard: Клавіатура (опціонально)

        Returns:
            True якщо повідомлення відправлено успішно, False інакше
        """
        pass 