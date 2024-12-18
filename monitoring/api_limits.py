from datetime import datetime, timedelta
import logging
from typing import Dict, List

class APILimitMonitor:
    def __init__(self):
        self.limits = {
            'birdeye': {
                'requests_per_second': 1,
                'alert_threshold': 0.8,  # 80%
                'window_size': timedelta(seconds=1)
            }
        }
        self.request_history: Dict[str, List[datetime]] = {
            'birdeye': []
        }
        self.logger = logging.getLogger('api_monitor')

    def record_request(self, api_name: str):
        """Записує новий запит до API"""
        now = datetime.now()
        self.request_history[api_name].append(now)
        self._cleanup_old_requests(api_name)
        self._check_limits(api_name)

    def _cleanup_old_requests(self, api_name: str):
        """Очищує старі запити поза вікном моніторингу"""
        window_start = datetime.now() - self.limits[api_name]['window_size']
        self.request_history[api_name] = [
            ts for ts in self.request_history[api_name]
            if ts > window_start
        ]

    def _check_limits(self, api_name: str):
        """Перевіряє чи не перевищено ліміти"""
        current_rate = len(self.request_history[api_name])
        max_rate = self.limits[api_name]['requests_per_second']
        threshold = max_rate * self.limits[api_name]['alert_threshold']

        if current_rate >= threshold:
            self._send_alert(api_name, current_rate, max_rate)

    def _send_alert(self, api_name: str, current_rate: int, max_rate: int):
        """Надсилає сповіщення про наближення до ліміту"""
        message = (
            f"⚠️ Увага! Наближаємося до ліміту {api_name} API\n"
            f"Поточна швидкість: {current_rate} запитів/сек\n"
            f"Максимальний ліміт: {max_rate} запитів/сек\n"
            f"Рекомендується розглянути оновлення до Pro тарифу"
        )
        self.logger.warning(message)
        # TODO: Додати відправку в Telegram 