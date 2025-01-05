# Конфігурація системи

## Загальні налаштування

### Мережа
```yaml
network:
  rpc_url: "https://api.mainnet-beta.solana.com"
  ws_url: "wss://api.mainnet-beta.solana.com"
  retry_delay: 5
  max_retries: 3
```

### API ключі
```yaml
api_keys:
  quicknode:
    key: "YOUR_QUICKNODE_API_KEY"
    secret: "YOUR_QUICKNODE_API_SECRET"
  jupiter:
    key: "YOUR_JUPITER_API_KEY"
```

### База даних
```yaml
database:
  host: "localhost"
  port: 5432
  name: "trading_bot"
  user: "trading_user"
  password: "secure_password"
  pool_size: 10
  timeout: 30
```

### Кешування
```yaml
redis:
  host: "localhost"
  port: 6379
  db: 0
  password: "redis_password"
  timeout: 5
```

## Торгові налаштування

### Ліміти
```yaml
limits:
  min_sol_balance: 0.1
  min_transaction_size: 0.01
  max_transaction_size: 10.0
  min_pool_liquidity: 1000
  max_slippage: 1.0
```

### Позиції
```yaml
positions:
  position_size_percent: 10
  max_positions: 5
  take_profit_levels: [1.5, 2.0, 3.0]
  stop_loss_level: 0.95
```

### Таймаути
```yaml
timeouts:
  transaction_confirmation: 60
  price_update: 5
  balance_update: 30
  session_duration: 86400
```

## Моніторинг

### Логування
```yaml
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "trading_bot.log"
  max_size: 10485760  # 10MB
  backup_count: 5
```

### Метрики
```yaml
metrics:
  enabled: true
  update_interval: 60
  storage_duration: 604800  # 7 days
  export_format: "csv"
```

### Сповіщення
```yaml
notifications:
  telegram:
    enabled: true
    bot_token: "YOUR_BOT_TOKEN"
    chat_id: "YOUR_CHAT_ID"
  email:
    enabled: false
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    sender: "bot@example.com"
    recipients: ["admin@example.com"]
```

## Безпека

### Шифрування
```yaml
encryption:
  key_file: "keys/encryption.key"
  algorithm: "AES-256-GCM"
  key_rotation_days: 30
```

### Доступ
```yaml
access:
  allowed_ips: ["127.0.0.1"]
  rate_limit: 100
  rate_window: 60
```

### Бекапи
```yaml
backups:
  enabled: true
  interval: 86400
  retention_days: 30
  storage_path: "backups/"
```

## Розширені налаштування

### Продуктивність
```yaml
performance:
  thread_pool_size: 4
  process_pool_size: 2
  batch_size: 100
  queue_size: 1000
```

### Відновлення
```yaml
recovery:
  enabled: true
  max_attempts: 3
  backoff_factor: 2
  initial_delay: 1
```

### Дебаг
```yaml
debug:
  enabled: false
  verbose_logging: false
  save_responses: false
  profile_calls: false
```

## Налаштування компонентів

### TradingManager
```yaml
trading_manager:
  max_concurrent_trades: 10
  health_check_interval: 60
  cleanup_interval: 3600
```

### SessionManager
```yaml
session_manager:
  session_timeout: 3600
  cleanup_interval: 86400
  max_sessions: 100
```

### WalletManager
```yaml
wallet_manager:
  update_interval: 30
  cache_duration: 300
  min_balance_alert: 1.0
```

### BlockchainSync
```yaml
blockchain_sync:
  sync_interval: 1
  max_blocks_behind: 10
  reorg_depth: 20
```

### WebSocketManager
```yaml
websocket_manager:
  ping_interval: 30
  reconnect_delay: 5
  max_message_size: 1048576
```

### PriceMonitor
```yaml
price_monitor:
  update_interval: 5
  cache_duration: 60
  volatility_window: 24
```

### TokenValidator
```yaml
token_validator:
  cache_duration: 3600
  min_holders: 100
  min_age_days: 7
``` 