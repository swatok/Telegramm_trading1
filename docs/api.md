# API та Інтерфейси

## Зовнішні API

### Jupiter API
```python
class JupiterAPI:
    async def get_price(self, token_address: str) -> Decimal:
        """Отримання ціни токену"""
        
    async def get_token_info(self, token_address: str) -> Dict:
        """Отримання інформації про токен"""
        
    async def get_pool_info(self, token_address: str) -> Dict:
        """Отримання інформації про пул ліквідності"""
        
    async def execute_swap(self, params: Dict) -> str:
        """Виконання свопу"""
```

### QuickNode API
```python
class QuickNodeAPI:
    async def get_sol_balance(self, address: str) -> Decimal:
        """Отримання балансу SOL"""
        
    async def get_token_balance(self, address: str, token: str) -> Decimal:
        """Отримання балансу токену"""
        
    async def get_transaction_status(self, tx_hash: str) -> Dict:
        """Отримання статусу транзакції"""
        
    async def subscribe_to_blocks(self) -> AsyncIterator[Dict]:
        """Підписка на нові блоки"""
```

## Внутрішні інтерфейси

### Торгові стратегії
```python
class TradingStrategy(Protocol):
    async def validate_signal(self, signal: Dict) -> bool:
        """Валідація торгового сигналу"""
        
    async def calculate_position_size(self, token: str, balance: Decimal) -> Dict:
        """Розрахунок розміру позиції"""
        
    async def get_entry_rules(self) -> Dict:
        """Правила входу в позицію"""
        
    async def get_exit_rules(self) -> Dict:
        """Правила виходу з позиції"""
```

### Валідатори
```python
class TokenValidator(Protocol):
    async def validate(self, token_address: str) -> Dict[str, bool]:
        """Валідація токену"""
        
class TradeValidator(Protocol):
    async def validate_buy(self, token: str, amount: Decimal) -> Dict[str, bool]:
        """Валідація покупки"""
        
    async def validate_sell(self, token: str, amount: Decimal) -> Dict[str, bool]:
        """Валідація продажу"""
```

### Моніторинг
```python
class PriceMonitor(Protocol):
    async def start_monitoring(self, token: str):
        """Початок моніторингу ціни"""
        
    async def stop_monitoring(self, token: str):
        """Зупинка моніторингу ціни"""
        
    def on_price_change(self, callback: Callable):
        """Підписка на зміни ціни"""
```

### Сховище даних
```python
class Repository(Protocol):
    async def add(self, item: Any) -> int:
        """Додавання запису"""
        
    async def get(self, id: int) -> Optional[Any]:
        """Отримання запису"""
        
    async def update(self, id: int, data: Dict) -> bool:
        """Оновлення запису"""
        
    async def delete(self, id: int) -> bool:
        """Видалення запису"""
```

## Події системи

### Торгові події
```python
class TradeEvent:
    SIGNAL_RECEIVED = "signal_received"
    POSITION_OPENED = "position_opened"
    POSITION_CLOSED = "position_closed"
    TAKE_PROFIT_TRIGGERED = "take_profit_triggered"
    STOP_LOSS_TRIGGERED = "stop_loss_triggered"
```

### Системні події
```python
class SystemEvent:
    STARTED = "system_started"
    STOPPED = "system_stopped"
    ERROR = "error_occurred"
    WARNING = "warning_occurred"
```

### Події блокчейну
```python
class BlockchainEvent:
    NEW_BLOCK = "new_block"
    TRANSACTION_CONFIRMED = "transaction_confirmed"
    TRANSACTION_FAILED = "transaction_failed"
```

## Розширення системи

### Додавання нового API
1. Створіть клас, що реалізує необхідний інтерфейс
2. Додайте фабрику для створення екземплярів
3. Оновіть конфігурацію для підтримки нового API

### Додавання нової стратегії
1. Створіть клас, що реалізує `TradingStrategy`
2. Додайте валідацію параметрів
3. Реалізуйте логіку розрахунків
4. Зареєструйте стратегію в системі

### Додавання нового валідатора
1. Створіть клас, що реалізує відповідний інтерфейс
2. Додайте необхідні перевірки
3. Інтегруйте з існуючими компонентами 