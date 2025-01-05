# Trading Bot

Автоматизований торговий бот для роботи з токенами Solana через Jupiter DEX.

## Структура проекту

```
Telegramm_trading1/
├── api/                    # API клієнти
│   ├── jupiter.py         # Клієнт Jupiter DEX
│   └── quicknode.py       # Клієнт QuickNode
├── database/              # Робота з базою даних
│   ├── models/            # Моделі даних
│   └── repositories/      # Репозиторії
├── trading/              # Торгові модулі
│   ├── blockchain_sync.py # Синхронізація з блокчейном
│   ├── config.py         # Конфігурація
│   ├── order_executor.py # Виконання ордерів
│   ├── position_manager.py # Управління позиціями
│   ├── price_calculator.py # Розрахунок цін
│   ├── price_monitor.py  # Моніторинг цін
│   ├── risk_manager.py   # Управління ризиками
│   ├── session_manager.py # Управління сесіями
│   ├── token_validator.py # Валідація токенів
│   ├── trade_validator.py # Валідація торгів
│   ├── trading_manager.py # Головний менеджер
│   └── websocket_manager.py # WebSocket з'єднання
└── utils/                # Утиліти
    ├── logger.py        # Логування
    └── config.py        # Загальні налаштування

```

## Залежності між модулями

### Основні компоненти:

1. `TradingManager` - головний координатор, який:
   - Ініціалізує та керує всіма компонентами
   - Обробляє торгові сигнали
   - Координує взаємодію між модулями

2. `SessionManager` - управління торговими сесіями:
   - Створення/закриття сесій
   - Відстеження активності
   - Збір метрик

3. `WalletManager` - робота з гаманцем:
   - Перевірка балансів
   - Управління токенами
   - Обгортання/розгортання SOL

4. `BlockchainSync` - синхронізація з блокчейном:
   - Моніторинг транзакцій
   - Оновлення статусів
   - Відстеження нових блоків

5. `PriceMonitor` - моніторинг цін:
   - Отримання актуальних цін
   - Відстеження змін
   - Перевірка ліквідності

## Налаштування

1. Встановіть залежності:
```bash
pip install -r requirements.txt
```

2. Налаштуйте змінні середовища:
```bash
export SOLANA_PRIVATE_KEY="your_private_key"
export QUICKNODE_RPC_URL="your_quicknode_url"
export JUPITER_API_KEY="your_jupiter_key"
```

3. Налаштуйте конфігурацію в `trading/config.py`:
- Мінімальний баланс
- Розмір позиції
- Рівні take-profit/stop-loss

## Використання

1. Запуск бота:
```python
from trading.trading_manager import TradingManager

# Ініціалізація менеджера
manager = TradingManager(
    jupiter_api=jupiter_api,
    quicknode_api=quicknode_api,
    position_repo=position_repo,
    trade_repo=trade_repo,
    transaction_repo=transaction_repo,
    wallet_address=wallet_address
)

# Запуск
await manager.start()
```

2. Обробка торгового сигналу:
```python
signal = {
    'token_address': 'token_address',
    'token_symbol': 'TOKEN',
    'take_profit': 2.5,  # 250%
    'stop_loss': -0.5    # -50%
}

success = await manager.handle_trade_signal(signal)
```

3. Зупинка бота:
```python
await manager.stop()
```

## Моніторинг

Бот надає детальне логування всіх операцій:
- Інформація про торги
- Статуси транзакцій
- Помилки та попередження

Логи зберігаються в `logs/trading.log`

## Безпека

1. Приватні ключі зберігаються тільки в змінних середовища
2. Використовується валідація всіх транзакцій
3. Реалізовано захист від помилкових торгів
4. Моніторинг підозрілих токенів

## Розширення

Система підтримує розширення через:
1. Додавання нових API клієнтів
2. Створення нових торгових стратегій
3. Реалізацію додаткових валідаторів
4. Інтеграцію з іншими DEX 