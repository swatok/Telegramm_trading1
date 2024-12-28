"""Trade model"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class Trade:
    """Клас для представлення торгової операції"""
    token_address: str
    amount: int
    quote: Dict[str, Any]
    status: str = "pending"
    signature: Optional[str] = None
    timestamp: datetime = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
            
    def update_status(self, status: str, error: str = None):
        """Оновлення статусу торгівлі"""
        self.status = status
        self.error = error 