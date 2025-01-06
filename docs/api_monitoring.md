# Моніторинг API

## Метрики

### Основні метрики

#### Метрики запитів
```python
class RequestMetrics:
    """Метрики HTTP запитів"""
    
    def __init__(self):
        self.total_requests = Counter(
            'api_requests_total',
            'Total number of API requests'
        )
        self.request_duration = Histogram(
            'api_request_duration_seconds',
            'Request duration in seconds'
        )
        self.request_size = Histogram(
            'api_request_size_bytes',
            'Request size in bytes'
        )
        
    def record_request(self, duration: float, size: int):
        """Запис метрик запиту"""
        self.total_requests.inc()
        self.request_duration.observe(duration)
        self.request_size.observe(size)
```

#### Метрики відповідей
```python
class ResponseMetrics:
    """Метрики HTTP відповідей"""
    
    def __init__(self):
        self.response_status = Counter(
            'api_response_status',
            'Response status codes',
            ['status']
        )
        self.response_time = Histogram(
            'api_response_time_seconds',
            'Response time in seconds'
        )
        self.response_size = Histogram(
            'api_response_size_bytes',
            'Response size in bytes'
        )
        
    def record_response(self, status: int, duration: float, size: int):
        """Запис метрик відповіді"""
        self.response_status.labels(status=status).inc()
        self.response_time.observe(duration)
        self.response_size.observe(size)
```

### Бізнес-метрики

#### Метрики торгівлі
```python
class TradingMetrics:
    """Метрики торгових операцій"""
    
    def __init__(self):
        self.trades_total = Counter(
            'trading_trades_total',
            'Total number of trades'
        )
        self.trade_volume = Counter(
            'trading_volume_total',
            'Total trading volume'
        )
        self.trade_success_rate = Gauge(
            'trading_success_rate',
            'Trade success rate'
        )
        
    def record_trade(self, amount: float, success: bool):
        """Запис метрик торгової операції"""
        self.trades_total.inc()
        self.trade_volume.inc(amount)
        self._update_success_rate(success)
```

## Логування

### Конфігурація логування

#### Налаштування логгера
```python
def setup_logging():
    """Налаштування системи логування"""
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
            'json': {
                'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
                'format': '%(asctime)s %(levelname)s %(name)s %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
                'level': 'INFO'
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'api.log',
                'formatter': 'json',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5
            }
        },
        'loggers': {
            '': {
                'handlers': ['console', 'file'],
                'level': 'INFO'
            }
        }
    })
```

### Логування запитів

#### Middleware логування
```python
class RequestLoggingMiddleware:
    """Middleware для логування запитів"""
    
    async def __call__(self, request: Request, call_next):
        """Обробка запиту"""
        # Початок запиту
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        # Логування запиту
        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host
            }
        )
        
        try:
            # Виконання запиту
            response = await call_next(request)
            
            # Логування відповіді
            duration = time.time() - start_time
            logger.info(
                "Request completed",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "duration": duration
                }
            )
            
            return response
            
        except Exception as e:
            # Логування помилки
            logger.error(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
```

## Сповіщення

### Налаштування сповіщень

#### Конфігурація сповіщень
```python
class AlertConfig:
    """Конфігурація системи сповіщень"""
    
    def __init__(self):
        self.thresholds = {
            "error_rate": 0.01,  # 1%
            "response_time": 1.0,  # 1 second
            "success_rate": 0.99  # 99%
        }
        self.channels = {
            "telegram": {
                "enabled": True,
                "chat_id": "YOUR_CHAT_ID",
                "bot_token": "YOUR_BOT_TOKEN"
            },
            "email": {
                "enabled": True,
                "recipients": ["admin@example.com"]
            }
        }
```

### Обробка подій

#### Генерація сповіщень
```python
class AlertManager:
    """Управління сповіщеннями"""
    
    async def process_metrics(self, metrics: Dict):
        """Обробка метрик та генерація сповіщень"""
        alerts = []
        
        # Перевірка помилок
        if metrics["error_rate"] > self.config.thresholds["error_rate"]:
            alerts.append(self._create_alert(
                level="error",
                title="High Error Rate",
                description=f"Error rate: {metrics['error_rate']:.2%}"
            ))
            
        # Перевірка часу відгуку
        if metrics["response_time"] > self.config.thresholds["response_time"]:
            alerts.append(self._create_alert(
                level="warning",
                title="High Response Time",
                description=f"Response time: {metrics['response_time']:.2f}s"
            ))
            
        # Відправка сповіщень
        for alert in alerts:
            await self._send_alert(alert)
```

## Візуалізація

### Графіки метрик

#### Генерація графіків
```python
class MetricsVisualizer:
    """Візуалізація метрик"""
    
    def create_request_chart(self, data: Dict):
        """Створення графіку запитів"""
        plt.figure(figsize=(12, 6))
        plt.plot(data["timestamps"], data["requests"])
        plt.title("API Requests Over Time")
        plt.xlabel("Time")
        plt.ylabel("Requests/sec")
        plt.grid(True)
        return plt
        
    def create_response_time_chart(self, data: Dict):
        """Створення графіку часу відгуку"""
        plt.figure(figsize=(12, 6))
        plt.plot(data["timestamps"], data["response_times"])
        plt.title("API Response Times")
        plt.xlabel("Time")
        plt.ylabel("Response Time (ms)")
        plt.grid(True)
        return plt
```

### Дашборди

#### Конфігурація Grafana
```python
class GrafanaDashboard:
    """Конфігурація дашборду Grafana"""
    
    def get_dashboard_config(self):
        """Отримання конфігурації дашборду"""
        return {
            "title": "API Monitoring",
            "panels": [
                {
                    "title": "Request Rate",
                    "type": "graph",
                    "datasource": "Prometheus",
                    "targets": [{
                        "expr": "rate(api_requests_total[5m])",
                        "legendFormat": "requests/sec"
                    }]
                },
                {
                    "title": "Response Times",
                    "type": "graph",
                    "datasource": "Prometheus",
                    "targets": [{
                        "expr": "rate(api_response_time_seconds_sum[5m])",
                        "legendFormat": "avg response time"
                    }]
                },
                {
                    "title": "Error Rate",
                    "type": "graph",
                    "datasource": "Prometheus",
                    "targets": [{
                        "expr": "rate(api_response_status{status=~'5..'}[5m])",
                        "legendFormat": "errors/sec"
                    }]
                }
            ]
        }
```

## Аналітика

### Аналіз трендів

#### Аналіз метрик
```python
class MetricsAnalyzer:
    """Аналіз метрик API"""
    
    async def analyze_trends(self, period: str = "1d"):
        """Аналіз трендів метрик"""
        metrics = await self._get_metrics(period)
        
        return {
            "request_trend": self._calculate_trend(
                metrics["requests"]
            ),
            "error_trend": self._calculate_trend(
                metrics["errors"]
            ),
            "performance_trend": self._calculate_trend(
                metrics["response_times"]
            )
        }
        
    def _calculate_trend(self, data: List[float]) -> Dict:
        """Розрахунок тренду"""
        return {
            "direction": "up" if data[-1] > data[0] else "down",
            "change": (data[-1] - data[0]) / data[0],
            "volatility": statistics.stdev(data)
        }
```

### Звіти

#### Генерація звітів
```python
class ReportGenerator:
    """Генерація звітів по API"""
    
    async def generate_daily_report(self):
        """Генерація щоденного звіту"""
        metrics = await self._get_daily_metrics()
        
        return {
            "summary": {
                "total_requests": metrics["total_requests"],
                "average_response_time": metrics["avg_response_time"],
                "error_rate": metrics["error_rate"],
                "success_rate": metrics["success_rate"]
            },
            "top_endpoints": await self._get_top_endpoints(),
            "error_summary": await self._get_error_summary(),
            "performance_stats": await self._get_performance_stats()
        }
``` 