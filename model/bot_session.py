"""
Модель для представлення сесії бота
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List, Any
from decimal import Decimal

@dataclass
class BotSession:
    id: str  # Унікальний ID сесії
    start_time: datetime  # Час початку сесії
    status: str  # running, paused, stopped, crashed
    
    # Статистика сесії
    processed_messages: int = 0  # Кількість оброблених повідомлень
    processed_signals: int = 0  # Кількість оброблених сигналів
    successful_trades: int = 0  # Кількість успішних угод
    failed_trades: int = 0  # Кількість невдалих угод
    
    # Фінансова статистика
    total_volume: Decimal = Decimal("0")  # Загальний об'єм торгів
    total_profit: Decimal = Decimal("0")  # Загальний прибуток
    total_fees: Decimal = Decimal("0")  # Загальні комісії
    
    # Помилки та попередження
    errors: List[Dict] = field(default_factory=list)  # Список помилок
    warnings: List[Dict] = field(default_factory=list)  # Список попереджень
    
    # Додаткова інформація
    config: Dict = field(default_factory=dict)  # Конфігурація сесії
    end_time: Optional[datetime] = None  # Час завершення сесії
    last_activity: Optional[datetime] = None  # Час останньої активності
    
    def __post_init__(self):
        """Валідація після створення"""
        valid_statuses = {'running', 'paused', 'stopped', 'crashed'}
        if self.status not in valid_statuses:
            raise ValueError(f"Невірний статус сесії: {self.status}")
            
    @property
    def is_active(self) -> bool:
        """Чи активна сесія"""
        return self.status == 'running'
        
    @property
    def duration_hours(self) -> float:
        """Тривалість сесії в годинах"""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds() / 3600
        
    @property
    def success_rate(self) -> float:
        """Відсоток успішних угод"""
        total_trades = self.successful_trades + self.failed_trades
        if total_trades == 0:
            return 0.0
        return (self.successful_trades / total_trades) * 100
        
    def add_error(self, error: str, details: Optional[Dict] = None):
        """Додавання помилки"""
        self.errors.append({
            "timestamp": datetime.now(),
            "error": error,
            "details": details
        })
        
    def add_warning(self, warning: str, details: Optional[Dict] = None):
        """Додавання попередження"""
        self.warnings.append({
            "timestamp": datetime.now(),
            "warning": warning,
            "details": details
        })
        
    def update_activity(self):
        """Оновлення часу останньої активності"""
        self.last_activity = datetime.now()
        
    def stop(self, reason: Optional[str] = None):
        """Зупинка сесії"""
        self.status = 'stopped'
        self.end_time = datetime.now()
        if reason:
            self.add_warning("Session stopped", {"reason": reason})
            
    def to_dict(self) -> dict:
        """Конвертація в словник для збереження"""
        return {
            "id": self.id,
            "start_time": self.start_time.isoformat(),
            "status": self.status,
            "processed_messages": self.processed_messages,
            "processed_signals": self.processed_signals,
            "successful_trades": self.successful_trades,
            "failed_trades": self.failed_trades,
            "total_volume": str(self.total_volume),
            "total_profit": str(self.total_profit),
            "total_fees": str(self.total_fees),
            "errors": self.errors,
            "warnings": self.warnings,
            "config": self.config,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None
        }
        
    def __str__(self) -> str:
        """Рядкове представлення сесії"""
        duration = f"{self.duration_hours:.1f}h"
        profit = f"profit={float(self.total_profit):.2f}"
        return (
            f"BotSession({self.id[:8]}, {self.status}, "
            f"duration={duration}, {profit})"
        ) 
        
    @property
    def is_running(self) -> bool:
        return self.status == 'running'
        
    def add_error(self, error_type: str, details: Dict[str, Any]):
        self.errors.append({
            'type': error_type,
            'details': details,
            'timestamp': datetime.now()
        }) 