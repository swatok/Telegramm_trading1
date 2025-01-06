# Моніторинг системи

## Метрики

### Системні метрики

#### Використання ресурсів
```python
class SystemMetrics:
    def collect_metrics(self):
        return {
            "cpu_usage": 45.2,  # %
            "memory_usage": 1.2,  # GB
            "disk_usage": 25.5,  # GB
            "network_in": 1024,  # KB/s
            "network_out": 512   # KB/s
        }
```

#### Продуктивність
```python
class PerformanceMetrics:
    def collect_metrics(self):
        return {
            "requests_per_second": 100,
            "average_response_time": 0.15,  # seconds
            "error_rate": 0.1,  # %
            "queue_size": 50
        }
```

### Торгові метрики

#### Статистика торгів
```python
class TradingMetrics:
    def collect_metrics(self):
        return {
            "total_trades": 1000,
            "successful_trades": 950,
            "failed_trades": 50,
            "average_profit": 2.5,  # %
            "total_volume": 100000  # USD
        }
```

#### Аналіз позицій
```python
class PositionMetrics:
    def collect_metrics(self):
        return {
            "open_positions": 5,
            "total_value": 50000,  # USD
            "unrealized_pnl": 1500,  # USD
            "average_holding_time": 3600  # seconds
        }
```

## Логування

### Рівні логування
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)
```

### Категорії логів

#### Торгові операції
```python
class TradingLogger:
    def log_trade(self, trade):
        logging.info(f"Trade executed: {trade}")
        
    def log_position(self, position):
        logging.info(f"Position updated: {position}")
        
    def log_balance(self, balance):
        logging.info(f"Balance changed: {balance}")
```

#### Системні події
```python
class SystemLogger:
    def log_startup(self):
        logging.info("System started")
        
    def log_shutdown(self):
        logging.info("System shutdown")
        
    def log_error(self, error):
        logging.error(f"Error occurred: {error}")
```

## Сповіщення

### Критичні події
```python
class AlertManager:
    def send_alert(self, level, message):
        if level == "critical":
            self._send_telegram_alert(message)
            self._send_email_alert(message)
            self._trigger_alarm()
```

### Канали сповіщень

#### Telegram
```python
class TelegramNotifier:
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        
    async def send_message(self, message):
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = {
            "chat_id": self.chat_id,
            "text": message
        }
        async with aiohttp.ClientSession() as session:
            await session.post(url, json=data)
```

#### Email
```python
class EmailNotifier:
    def __init__(self, smtp_config):
        self.smtp_config = smtp_config
        
    def send_email(self, subject, body):
        with smtplib.SMTP(self.smtp_config["server"]) as server:
            server.starttls()
            server.login(self.smtp_config["user"], self.smtp_config["password"])
            msg = MIMEText(body)
            msg["Subject"] = subject
            server.send_message(msg)
```

## Візуалізація

### Графіки

#### Торгові графіки
```python
class TradingCharts:
    def plot_price_chart(self, data):
        """Графік цін"""
        plt.figure(figsize=(12, 6))
        plt.plot(data["timestamps"], data["prices"])
        plt.title("Price Chart")
        plt.xlabel("Time")
        plt.ylabel("Price")
        plt.grid(True)
        plt.show()
        
    def plot_volume_chart(self, data):
        """Графік об'ємів"""
        plt.figure(figsize=(12, 6))
        plt.bar(data["timestamps"], data["volumes"])
        plt.title("Volume Chart")
        plt.xlabel("Time")
        plt.ylabel("Volume")
        plt.show()
```

#### Метрики продуктивності
```python
class PerformanceCharts:
    def plot_response_times(self, data):
        """Графік часу відгуку"""
        plt.figure(figsize=(12, 6))
        plt.plot(data["timestamps"], data["response_times"])
        plt.title("Response Times")
        plt.xlabel("Time")
        plt.ylabel("Response Time (ms)")
        plt.grid(True)
        plt.show()
        
    def plot_error_rates(self, data):
        """Графік помилок"""
        plt.figure(figsize=(12, 6))
        plt.plot(data["timestamps"], data["error_rates"])
        plt.title("Error Rates")
        plt.xlabel("Time")
        plt.ylabel("Error Rate (%)")
        plt.grid(True)
        plt.show()
```

## Дашборди

### Торговий дашборд
```python
class TradingDashboard:
    def render(self):
        return {
            "portfolio": self.get_portfolio_summary(),
            "active_trades": self.get_active_trades(),
            "performance": self.get_performance_metrics(),
            "alerts": self.get_active_alerts()
        }
        
    def get_portfolio_summary(self):
        return {
            "total_value": 100000,
            "daily_pnl": 1500,
            "open_positions": 5
        }
```

### Системний дашборд
```python
class SystemDashboard:
    def render(self):
        return {
            "system_health": self.get_system_health(),
            "resource_usage": self.get_resource_usage(),
            "error_logs": self.get_recent_errors(),
            "performance": self.get_performance_stats()
        }
        
    def get_system_health(self):
        return {
            "status": "healthy",
            "uptime": "5d 12h",
            "last_error": "2d ago"
        }
```

## Аналітика

### Торгова аналітика
```python
class TradingAnalytics:
    def analyze_performance(self):
        return {
            "win_rate": 65.5,  # %
            "average_profit": 2.5,  # %
            "sharpe_ratio": 1.8,
            "max_drawdown": 15.2  # %
        }
        
    def analyze_strategy(self):
        return {
            "best_pair": "SOL/USDC",
            "best_time": "14:00-16:00",
            "worst_pair": "RAY/USDC",
            "risk_level": "medium"
        }
```

### Ризик-менеджмент
```python
class RiskAnalytics:
    def analyze_risks(self):
        return {
            "var_95": 5000,  # Value at Risk
            "position_concentration": 25.5,  # %
            "liquidity_risk": "low",
            "market_risk": "medium"
        }
        
    def generate_alerts(self):
        return [
            {"level": "warning", "message": "High concentration in SOL"},
            {"level": "info", "message": "Approaching daily limit"}
        ]
```

## Звіти

### Щоденний звіт
```python
class DailyReport:
    def generate(self):
        return {
            "date": "2023-10-20",
            "summary": {
                "total_trades": 100,
                "profit_loss": 1500,
                "win_rate": 65
            },
            "details": {
                "best_trade": {"pair": "SOL/USDC", "profit": 500},
                "worst_trade": {"pair": "RAY/USDC", "loss": -200}
            }
        }
```

### Тижневий звіт
```python
class WeeklyReport:
    def generate(self):
        return {
            "week": "2023-W42",
            "summary": {
                "total_volume": 1000000,
                "net_profit": 15000,
                "average_daily_trades": 120
            },
            "analysis": {
                "best_day": "Wednesday",
                "worst_day": "Friday",
                "trend": "upward"
            }
        } 