"""
Модель для представлення каналу моніторингу
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List
from decimal import Decimal

@dataclass
class Channel:
    id: int  # ID каналу
    name: str  # Назва каналу
    type: str  # telegram, twitter, etc.
    status: str  # active, paused, disabled
    
    # Статистика
    success_rate: float = 0.0  # Відсоток успішних сигналів
    signals_count: int = 0  # Кількість сигналів
    last_signal: Optional[datetime] = None  # Час останнього сигналу
    
    # Налаштування
    settings: Dict[str, any] = field(default_factory=dict)  # Налаштування каналу
    
    # Розширена статистика
    successful_signals: int = 0  # Кількість успішних сигналів
    failed_signals: int = 0  # Кількість невдалих сигналів
    total_profit: Decimal = Decimal("0")  # Загальний прибуток
    average_profit: Decimal = Decimal("0")  # Середній прибуток
    
    # Історія сигналів
    signal_history: List[Dict] = field(default_factory=list)  # Історія останніх сигналів
    
    def __post_init__(self):
        """Валідація після створення"""
        valid_types = {'telegram', 'twitter', 'discord'}
        if self.type not in valid_types:
            raise ValueError(f"Невірний тип каналу: {self.type}")
            
        valid_statuses = {'active', 'paused', 'disabled'}
        if self.status not in valid_statuses:
            raise ValueError(f"Невірний статус каналу: {self.status}")
            
    @property
    def is_active(self) -> bool:
        """Чи активний канал"""
        return self.status == 'active'
        
    @property
    def last_signal_age_hours(self) -> Optional[float]:
        """Вік останнього сигналу в годинах"""
        if not self.last_signal:
            return None
        return (datetime.now() - self.last_signal).total_seconds() / 3600
        
    def add_signal_result(self, success: bool, profit: Optional[Decimal] = None):
        """Додавання результату сигналу"""
        self.signals_count += 1
        if success:
            self.successful_signals += 1
            if profit:
                self.total_profit += profit
        else:
            self.failed_signals += 1
            
        self.success_rate = (self.successful_signals / self.signals_count) * 100
        if self.successful_signals > 0:
            self.average_profit = self.total_profit / self.successful_signals
            
    def add_to_history(self, signal_data: Dict):
        """Додавання сигналу в історію"""
        self.signal_history.append({
            **signal_data,
            "timestamp": datetime.now()
        })
        self.last_signal = datetime.now()
        
        # Обмежуємо історію останніми 100 сигналами
        if len(self.signal_history) > 100:
            self.signal_history = self.signal_history[-100:]
            
    def to_dict(self) -> dict:
        """Конвертація в словник для збереження"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "status": self.status,
            "success_rate": self.success_rate,
            "signals_count": self.signals_count,
            "last_signal": self.last_signal.isoformat() if self.last_signal else None,
            "settings": self.settings,
            "successful_signals": self.successful_signals,
            "failed_signals": self.failed_signals,
            "total_profit": str(self.total_profit),
            "average_profit": str(self.average_profit),
            "signal_history": self.signal_history
        }
        
    def __str__(self) -> str:
        """Рядкове представлення каналу"""
        return (
            f"Channel({self.name}, {self.type}, "
            f"success_rate={self.success_rate:.1f}%, signals={self.signals_count})"
        ) 