"""Константи для роботи з Jupiter API"""

# Адреси системних токенів
WSOL_ADDRESS = "So11111111111111111111111111111111111111112"
USDC_ADDRESS = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
USDT_ADDRESS = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"

# Ендпоінти API
API_ENDPOINTS = {
    "v6": {
        "quote": "https://quote-api.jup.ag/v6",
        "price": "https://price.jup.ag/v6",
        "swap": "https://quote-api.jup.ag/v6/swap",
    },
    "v4": {
        "quote": "https://quote-api.jup.ag/v4",
        "price": "https://price.jup.ag/v4",
        "swap": "https://quote-api.jup.ag/v4/swap",
    }
}

TOKEN_LIST_ENDPOINT = "https://token.jup.ag/all"

# Параметри за замовчуванням
DEFAULT_SLIPPAGE = 1.0  # 1%
MAX_ACCOUNTS_PER_ROUTE = 64
DEFAULT_TIMEOUT = 30  # секунд

# Параметри повторних спроб
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # секунд

# Параметри кешування
CACHE_TTL = 300  # 5 хвилин
PRICE_CACHE_TTL = 60  # 1 хвилина

# Параметри WebSocket
WS_RECONNECT_DELAY = 5  # секунд
WS_PING_INTERVAL = 30  # секунд
WS_PING_TIMEOUT = 10  # секунд

# Параметри валідації
MIN_LIQUIDITY_USD = 1000  # мінімальна ліквідність в USD
MIN_VOLUME_24H_USD = 100  # мінімальний об'єм за 24 години в USD
MAX_PRICE_IMPACT = 5.0  # максимальний вплив на ціну в %

# Параметри моніторингу
HEALTH_CHECK_INTERVAL = 60  # секунд
PRICE_UPDATE_INTERVAL = 1  # секунд

# Параметри транзакцій
MAX_PRIORITY_FEE = 100  # максимальна пріоритетна комісія в lamports
MAX_COMPUTE_UNITS = 200_000  # максимальна кількість compute units

# Статуси транзакцій
class TransactionStatus:
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    TIMEOUT = "timeout"

# Типи ордерів
class OrderType:
    MARKET = "market"
    LIMIT = "limit"

# Напрямки торгівлі
class TradeDirection:
    BUY = "buy"
    SELL = "sell"

# Коди помилок
class ErrorCode:
    INSUFFICIENT_FUNDS = "insufficient_funds"
    PRICE_IMPACT_HIGH = "price_impact_high"
    SLIPPAGE_EXCEEDED = "slippage_exceeded"
    ROUTE_NOT_FOUND = "route_not_found"
    TOKEN_NOT_FOUND = "token_not_found"
    INVALID_ADDRESS = "invalid_address"
    NETWORK_ERROR = "network_error"
    API_ERROR = "api_error" 