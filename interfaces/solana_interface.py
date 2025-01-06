from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class SolanaInterface(ABC):
    """Інтерфейс для роботи з Solana"""

    @abstractmethod
    async def connect_to_network(self, endpoint: str) -> bool:
        """
        Підключення до мережі Solana

        Args:
            endpoint: URL ноди Solana

        Returns:
            True якщо підключення успішне, False інакше
        """
        pass

    @abstractmethod
    async def get_contract_info(self, contract_address: str) -> Dict[str, Any]:
        """
        Отримання інформації про смарт-контракт

        Args:
            contract_address: Адреса контракту

        Returns:
            Інформація про контракт
        """
        pass

    @abstractmethod
    async def check_liquidity(self, token_address: str) -> float:
        """
        Перевірка ліквідності токена

        Args:
            token_address: Адреса токена

        Returns:
            Об'єм ліквідності
        """
        pass

    @abstractmethod
    async def execute_swap(self, 
                         token_address: str,
                         amount: float,
                         slippage: float) -> Optional[Dict[str, Any]]:
        """
        Виконання swap операції

        Args:
            token_address: Адреса токена
            amount: Кількість для обміну
            slippage: Допустимий відсоток проковзування

        Returns:
            Результат операції або None при помилці
        """
        pass 