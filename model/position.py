"""
Модель для представлення торгової позиції
"""
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime
from typing import Optional, List, Dict
from .token import Token

@dataclass
class Position:
    token: Token  # Токен позиції
    entry_price: Decimal  # Ціна входу
    amount: Decimal  # Кількість токенів
    entry_time: datetime  # Час входу
    status: str  # active, closed, liquidated
    
    # Рівні виходу
    take_profits: List[Dict[str, Decimal]] = field(default_factory=list)  # [{"level": 2.0, "amount": 0.5}, ...]
    stop_loss: Optional[Decimal] = None  # Рівень стоп-лосу
    
    # Поточний стан
    current_price: Optional[Decimal] = None  # Поточна ціна
    pnl: Optional[Decimal] = None  # Прибуток/збиток
    last_update: Optional[datetime] = None  # Останнє оновлення
    
    # Історія торгів
    executed_take_profits: List[Dict] = field(default_factory=list)  # Виконані take-profit ��рдери
    remaining_amount: Optional[Decimal] = None  # Залишок токенів
    
    def __post_init__(self):
        """Валідація після створення"""
        valid_statuses = {'active', 'closed', 'liquidated'}
        if self.status not in valid_statuses:
            raise ValueError(f"Невірний статус позиції: {self.status}")
        if self.remaining_amount is None:
            self.remaining_amount = self.amount
            
    @property
    def is_active(self) -> bool:
        """Чи активна позиція"""
        return self.status == 'active'
        
    @property
    def age_hours(self) -> float:
        """Вік позиції в годинах"""
        return (datetime.now() - self.entry_time).total_seconds() / 3600
        
    @property
    def current_pnl_percent(self) -> Optional[Decimal]:
        """Поточний P&L у відсотках"""
        if not self.current_price or not self.entry_price:
            return None
        return (self.current_price - self.entry_price) / self.entry_price * Decimal("100")
        
    def update_price(self, new_price: Decimal):
        """Оновлення поточної ціни"""
        self.current_price = new_price
        self.last_update = datetime.now()
        if self.entry_price:
            self.pnl = (new_price - self.entry_price) * self.remaining_amount
            
    def execute_take_profit(self, price: Decimal, amount: Decimal):
        """Виконання take-profit"""
        if amount > self.remaining_amount:
            raise ValueError("Недостатньо токенів для виконання take-profit")
            
        self.executed_take_profits.append({
            "price": price,
            "amount": amount,
            "timestamp": datetime.now()
        })
        self.remaining_amount -= amount
        
        if self.remaining_amount == 0:
            self.status = 'closed'
            
    def to_dict(self) -> dict:
        """Конвертація в словник для збереження"""
        return {
            "token": self.token.to_dict(),
            "entry_price": str(self.entry_price),
            "amount": str(self.amount),
            "entry_time": self.entry_time.isoformat(),
            "status": self.status,
            "take_profits": [{
                "level": str(tp["level"]),
                "amount": str(tp["amount"])
            } for tp in self.take_profits],
            "stop_loss": str(self.stop_loss) if self.stop_loss else None,
            "current_price": str(self.current_price) if self.current_price else None,
            "pnl": str(self.pnl) if self.pnl else None,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "executed_take_profits": [{
                "price": str(tp["price"]),
                "amount": str(tp["amount"]),
                "timestamp": tp["timestamp"].isoformat()
            } for tp in self.executed_take_profits],
            "remaining_amount": str(self.remaining_amount) if self.remaining_amount else None
        }
        
    def __str__(self) -> str:
        """Рядкове представлення позиції"""
        pnl_str = f", PNL: {float(self.pnl):.2f}" if self.pnl else ""
        return (
            f"Position({self.token.symbol}, {self.status}, "
            f"amount={float(self.remaining_amount):.4f}{pnl_str})"
        ) 