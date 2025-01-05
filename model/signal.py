"""
Модель для представлення торгового сигналу
"""
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from typing import Optional, List
from .token import Token

@dataclass
class Signal:
    # Основна інформація
    token_address: str  # Адреса токену
    action: str  # 'buy' або 'sell'
    timestamp: datetime  # Час отримання сигналу
    
    # Джерело сигналу
    source_type: str  # 'telegram', 'twitter', etc.
    source_id: str  # ID каналу/користувача
    message_id: Optional[int] = None  # ID повідомлення
    
    # Параметри торгівлі
    entry_price: Optional[Decimal] = None  # Ціна входу
    target_prices: List[Decimal] = None  # Цілі по ціні
    stop_loss: Optional[Decimal] = None  # Стоп-лосс
    amount_sol: Optional[Decimal] = None  # Сума в SOL
    slippage: Decimal = Decimal("1.0")  # Допустимий slippage в %
    
    # Метадані токену
    token: Optional[Token] = None  # Об'єкт токену
    market_cap: Optional[Decimal] = None  # Капіталізація
    volume_24h: Optional[Decimal] = None  # Об'єм за 24 години
    holders: Optional[int] = None  # Кількість холдерів
    
    # Аналітика
    confidence_score: Decimal = Decimal("0")  # Оцінка впевненості (0-1)
    risk_score: Decimal = Decimal("0")  # Оцінка ризику (0-1)
    sentiment_score: Optional[Decimal] = None  # Оцінка настроїв (-1 до 1)
    
    # Статус обробки
    status: str = "new"  # new, processing, executed, failed, cancelled
    execution_price: Optional[Decimal] = None  # Ціна виконання
    execution_time: Optional[datetime] = None  # Час виконання
    transaction_signature: Optional[str] = None  # Підпис транзакції
    error_message: Optional[str] = None  # Повідомлення про помилку
    
    def __post_init__(self):
        """Ініціалізація після створення"""
        if self.target_prices is None:
            self.target_prices = []
            
    @property
    def is_buy(self) -> bool:
        """Чи є сигнал на покупку"""
        return self.action.lower() == 'buy'
        
    @property
    def is_executed(self) -> bool:
        """Чи виконано сигнал"""
        return self.status == "executed"
        
    @property
    def age_minutes(self) -> float:
        """Вік сигналу в хвилинах"""
        if not self.timestamp:
            return 0
        delta = datetime.now() - self.timestamp
        return delta.total_seconds() / 60
        
    def update_status(self, new_status: str, error: Optional[str] = None):
        """Оновлення статусу сигналу"""
        self.status = new_status
        if error:
            self.error_message = error
        if new_status == "executed":
            self.execution_time = datetime.now()
            
    def to_dict(self) -> dict:
        """Конвертація в словник для збереження"""
        return {
            "token_address": self.token_address,
            "action": self.action,
            "timestamp": self.timestamp.isoformat(),
            "source_type": self.source_type,
            "source_id": self.source_id,
            "message_id": self.message_id,
            "entry_price": str(self.entry_price) if self.entry_price else None,
            "target_prices": [str(p) for p in self.target_prices] if self.target_prices else [],
            "stop_loss": str(self.stop_loss) if self.stop_loss else None,
            "amount_sol": str(self.amount_sol) if self.amount_sol else None,
            "slippage": str(self.slippage),
            "token": self.token.to_dict() if self.token else None,
            "market_cap": str(self.market_cap) if self.market_cap else None,
            "volume_24h": str(self.volume_24h) if self.volume_24h else None,
            "holders": self.holders,
            "confidence_score": str(self.confidence_score),
            "risk_score": str(self.risk_score),
            "sentiment_score": str(self.sentiment_score) if self.sentiment_score else None,
            "status": self.status,
            "execution_price": str(self.execution_price) if self.execution_price else None,
            "execution_time": self.execution_time.isoformat() if self.execution_time else None,
            "transaction_signature": self.transaction_signature,
            "error_message": self.error_message
        }
        
    def __str__(self) -> str:
        """Рядкове представлення сигналу"""
        token_info = self.token.symbol if self.token else self.token_address[:8]
        return (
            f"Signal({self.action.upper()}, {token_info}, "
            f"status={self.status}, confidence={float(self.confidence_score):.2f})"
        ) 