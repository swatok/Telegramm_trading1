"""Signal model"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Signal:
    """Клас для представлення торгового сигналу"""
    token_address: str
    timestamp: datetime = None
    status: str = "pending"
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
            
    def update_status(self, status: str, error: str = None):
        """Оновлення статусу сигналу"""
        self.status = status
        self.error = error 