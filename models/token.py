"""Token model"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class Token:
    """Клас для представлення інформації про токен"""
    address: str
    symbol: str
    name: str
    decimals: int
    logo_uri: Optional[str] = None
    price: Optional[float] = None
    balance: Optional[float] = None 