# Telegram Trading Bot

Бот для автоматичної торгівлі на Solana через Jupiter API на основі сигналів з Telegram каналів.

## Особливості

- Моніторинг Telegram каналів для пошуку торгових сигналів
- Автоматичне виконання свопів через Jupiter API
- Взаємодія з блокчейном Solana через QuickNode
- Детальна статистика торгів та активності
- Логування всіх операцій
- Telegram сповіщення про всі дії

## Структура проекту

```
telegram_trading_bot/
├── api/                    # API клієнти
│   ├── jupiter.py         # Jupiter API клієнт
│   └── quicknode.py       # QuickNode API клієнт
├── model/                  # Моделі даних
│   ├── token.py           # Модель токену
│   ├── signal.py          # Модель торгового сигналу
│   ├── transaction.py     # Модель транз��кції
│   └── ...
├── monitoring/            # Моніторинг та статистика
├── main.py               # Головний файл
├── trading.py            # Торгова логіка
└── message_parser.py     # Парсер повідомлень
```

## Встановлення

1. Клонуйте репозиторій:
```bash
git clone https://github.com/yourusername/telegram_trading_bot.git
cd telegram_trading_bot
```

2. Створіть віртуальне середовище та встановіть залежності:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# або
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

3. Створіть файл `.env` з налаштуваннями:
```env
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=your_phone
TELEGRAM_SESSION_NAME=user_session
MONITOR_CHANNEL_ID=your_monitor_channel_id
SOURCE_CHANNELS=["@channel1", "@channel2"]
SOLANA_PRIVATE_KEY=your_solana_private_key
```

## Використання

Запустіть бота:
```bash
python main.py
```

## Безпека

- Ніколи не публікуйте ваш `.env` файл
- Зберігайте приватні ключі в безпечному місці
- Використовуйте окремий гаманець для торгівлі
- Встановлюйте ліміти на торгові операції

## Ліцензія

MIT 