"""Константи для змінних оточення"""

# Обов'язкові змінні оточення
REQUIRED_ENV_VARS = [
    'API_ID',
    'API_HASH', 
    'BOT_TOKEN',
    'ADMIN_ID',
    'PHONE',
    'QUICKNODE_WSS_URL',
    'QUICKNODE_HTTP_URL', 
    'WALLET_PRIVATE_KEY',
    'MONITOR_CHANNEL_ID',
    'SOURCE_CHANNELS'
]

# Значення за замовчуванням для торгівлі
DEFAULT_MAX_SLIPPAGE = 1.0  # %
DEFAULT_MIN_LIQUIDITY = 0.05  # SOL
DEFAULT_POSITION_PERCENT = 5.0  # %
DEFAULT_MAX_FDV = 40000  # USD
DEFAULT_TAKE_PROFIT = 10.0  # %
DEFAULT_STOP_LOSS = 5.0  # %

# Значення за замовчуванням для моніторингу
DEFAULT_PRICE_UPDATE_INTERVAL = 10  # секунди
DEFAULT_POSITION_CHECK_INTERVAL = 30  # секунди
DEFAULT_RECONNECT_DELAY = 5  # секунди
DEFAULT_MAX_RECONNECT_ATTEMPTS = 3

# Значення за замовчуванням для Telegram
DEFAULT_SESSION_PATH = 'sessions/'
DEFAULT_MONITOR_SESSION = 'monitor_session'
DEFAULT_BOT_SESSION = 'bot_session'
DEFAULT_SOURCE_CHANNELS = '[]'

# Значення за замовчуванням для логування
DEFAULT_LOG_LEVEL = 'INFO'
DEFAULT_LOG_FILE_PATH = 'logs/trading_bot.log'
DEFAULT_LOG_FORMAT = '{time} | {level} | {module}:{function}:{line} - {message}'
DEFAULT_LOG_ROTATION = '1 day'
DEFAULT_LOG_COMPRESSION = 'zip' 