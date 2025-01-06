"""
Модуль для відстеження метрик продуктивності торгової системи.
"""

from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import statistics

from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class PerformanceMetrics:
    """
    Клас для збору та аналізу метрик продуктивності.
    Відстежує різні аспекти роботи торгової системи.
    """

    def __init__(self):
        """Ініціалізація системи метрик."""
        self._api_calls: Dict[str, List[float]] = {}
        self._trades: List[Dict] = []
        self._errors: List[Dict] = []
        self._start_time = datetime.now()

    def record_api_call(self, endpoint: str, response_time: float, success: bool):
        """
        Запис метрик API виклику.

        Args:
            endpoint: Назва ендпоінту
            response_time: Час відповіді в секундах
            success: Чи був виклик успішним
        """
        if endpoint not in self._api_calls:
            self._api_calls[endpoint] = []
        
        self._api_calls[endpoint].append(response_time)
        
        if not success:
            self._errors.append({
                'type': 'api_error',
                'endpoint': endpoint,
                'time': datetime.now(),
                'response_time': response_time
            })

    def record_trade(
        self,
        token_address: str,
        amount: Decimal,
        price: Decimal,
        trade_type: str,
        success: bool,
        error: Optional[str] = None
    ):
        """
        Запис інформації про торгову операцію.

        Args:
            token_address: Адреса токену
            amount: Кількість токенів
            price: Ціна операції
            trade_type: Тип операції (buy/sell)
            success: Чи була операція успішною
            error: Опис помилки, якщо була
        """
        trade_info = {
            'token_address': token_address,
            'amount': float(amount),
            'price': float(price),
            'type': trade_type,
            'success': success,
            'time': datetime.now()
        }
        
        self._trades.append(trade_info)
        
        if not success and error:
            self._errors.append({
                'type': 'trade_error',
                'token_address': token_address,
                'error': error,
                'time': datetime.now()
            })

    def record_error(self, error_type: str, details: str):
        """
        Запис помилки.

        Args:
            error_type: Тип помилки
            details: Деталі помилки
        """
        self._errors.append({
            'type': error_type,
            'details': details,
            'time': datetime.now()
        })

    def get_api_stats(self) -> Dict:
        """
        Отримання статистики API викликів.

        Returns:
            Словник зі статистикою API викликів
        """
        stats = {}
        for endpoint, times in self._api_calls.items():
            if not times:
                continue
                
            stats[endpoint] = {
                'total_calls': len(times),
                'average_time': statistics.mean(times),
                'min_time': min(times),
                'max_time': max(times),
                'median_time': statistics.median(times)
            }
        return stats

    def get_trade_stats(self) -> Dict:
        """
        Отримання торгової статистики.

        Returns:
            Словник з торговою статистикою
        """
        successful_trades = [t for t in self._trades if t['success']]
        failed_trades = [t for t in self._trades if not t['success']]
        
        return {
            'total_trades': len(self._trades),
            'successful_trades': len(successful_trades),
            'failed_trades': len(failed_trades),
            'success_rate': len(successful_trades) / len(self._trades) if self._trades else 0
        }

    def get_error_stats(self) -> Dict:
        """
        Отримання статистики помилок.

        Returns:
            Словник зі статистикою помилок
        """
        error_counts = {}
        for error in self._errors:
            error_type = error['type']
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
            
        return {
            'total_errors': len(self._errors),
            'error_types': error_counts,
            'recent_errors': self._errors[-10:] if self._errors else []
        }

    def get_performance_summary(self) -> Dict:
        """
        Отримання загального звіту про продуктивність.

        Returns:
            Словник із загальною статистикою
        """
        uptime = datetime.now() - self._start_time
        
        return {
            'uptime': str(uptime),
            'uptime_seconds': uptime.total_seconds(),
            'api_stats': self.get_api_stats(),
            'trade_stats': self.get_trade_stats(),
            'error_stats': self.get_error_stats()
        }

    def get_hourly_stats(self) -> List[Dict]:
        """
        Отримання погодинної статистики.

        Returns:
            Список зі статистикою по годинах
        """
        hourly_stats = []
        current_time = datetime.now()
        
        for hour in range(24):
            hour_start = current_time - timedelta(hours=hour+1)
            hour_end = current_time - timedelta(hours=hour)
            
            hour_trades = [
                t for t in self._trades
                if hour_start <= t['time'] <= hour_end
            ]
            
            hour_errors = [
                e for e in self._errors
                if hour_start <= e['time'] <= hour_end
            ]
            
            hourly_stats.append({
                'hour': hour_start.strftime('%Y-%m-%d %H:00'),
                'trades': len(hour_trades),
                'successful_trades': len([t for t in hour_trades if t['success']]),
                'errors': len(hour_errors)
            })
            
        return hourly_stats

    def clear_old_data(self, days: int = 7):
        """
        Очищення старих даних.

        Args:
            days: Кількість днів даних для зберігання
        """
        cutoff_time = datetime.now() - timedelta(days=days)
        
        self._trades = [
            t for t in self._trades
            if t['time'] > cutoff_time
        ]
        
        self._errors = [
            e for e in self._errors
            if e['time'] > cutoff_time
        ]
        
        logger.info(f"Очищено дані старіші за {days} днів") 