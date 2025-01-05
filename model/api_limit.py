"""
Модель для представлення лімітів API
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, List

@dataclass
class APILimit:
    api_name: str  # Назва API (jupiter, quicknode, etc.)
    endpoint: str  # Назва ендпоінту
    limit_type: str  # requests_per_second, requests_per_minute, etc.
    max_requests: int  # Максимальна кількість запитів
    window_seconds: int  # Розмір вікна в секундах
    
    # Лічильники
    current_requests: int = 0
    total_requests: int = 0
    window_start: Optional[datetime] = None
    
    # Історія запитів
    request_history: List[datetime] = field(default_factory=list)
    error_history: List[Dict] = field(default_factory=list)
    
    def __post_init__(self):
        """Валідація після створення"""
        valid_limit_types = {
            'requests_per_second',
            'requests_per_minute',
            'requests_per_hour',
            'requests_per_day'
        }
        if self.limit_type not in valid_limit_types:
            raise ValueError(f"Невірний тип ліміту: {self.limit_type}")
            
        self.window_start = datetime.now()
        
    @property
    def remaining_requests(self) -> int:
        """Кількість запитів, що залишилися"""
        self._cleanup_old_requests()
        return max(0, self.max_requests - self.current_requests)
        
    @property
    def is_limited(self) -> bool:
        """Чи досягнуто ліміт"""
        return self.remaining_requests == 0
        
    @property
    def reset_time(self) -> datetime:
        """Час скидання лічильника"""
        if not self.window_start:
            return datetime.now()
        return self.window_start + timedelta(seconds=self.window_seconds)
        
    def _cleanup_old_requests(self):
        """Очищення старих запитів"""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.window_seconds)
        
        # Видалення старих запитів
        self.request_history = [
            ts for ts in self.request_history 
            if ts > cutoff
        ]
        self.current_requests = len(self.request_history)
        
        # Онов��ення вікна якщо потрібно
        if not self.window_start or self.window_start < cutoff:
            self.window_start = now
            
    def add_request(self):
        """Додавання нового запиту"""
        self._cleanup_old_requests()
        
        if self.is_limited:
            raise ValueError(
                f"Досягнуто ліміт запитів для {self.api_name}/{self.endpoint}"
            )
            
        now = datetime.now()
        self.request_history.append(now)
        self.current_requests += 1
        self.total_requests += 1
        
    def add_error(self, error: str, details: Optional[Dict] = None):
        """Додавання помилки"""
        self.error_history.append({
            "timestamp": datetime.now(),
            "error": error,
            "details": details
        })
        
    def get_usage_stats(self) -> Dict:
        """Отримання статистики використання"""
        self._cleanup_old_requests()
        return {
            "current_requests": self.current_requests,
            "total_requests": self.total_requests,
            "remaining_requests": self.remaining_requests,
            "is_limited": self.is_limited,
            "reset_time": self.reset_time.isoformat(),
            "error_count": len(self.error_history)
        }
        
    def to_dict(self) -> dict:
        """Конвертація в словник для збереження"""
        return {
            "api_name": self.api_name,
            "endpoint": self.endpoint,
            "limit_type": self.limit_type,
            "max_requests": self.max_requests,
            "window_seconds": self.window_seconds,
            "current_requests": self.current_requests,
            "total_requests": self.total_requests,
            "window_start": self.window_start.isoformat() if self.window_start else None,
            "request_history": [ts.isoformat() for ts in self.request_history],
            "error_history": self.error_history
        }
        
    def __str__(self) -> str:
        """Рядкове представлення ліміту"""
        return (
            f"APILimit({self.api_name}/{self.endpoint}, "
            f"{self.current_requests}/{self.max_requests} requests)"
        ) 