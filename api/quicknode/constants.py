from enum import IntEnum, Enum
from os import getenv
from typing import Optional, List
import re
import logging

# Системні токени
WSOL_ADDRESS = "So11111111111111111111111111111111111111112"
TOKEN_PROGRAM_ID = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"

# Ендпоінти за замовчуванням
DEFAULT_ENDPOINTS = [
    "https://api.mainnet-beta.solana.com",
    "https://solana-mainnet.g.alchemy.com/v2/your-api-key",
    "https://solana-api.projectserum.com"
]

# Параметри за замовчуванням
DEFAULT_COMMITMENT = "confirmed"
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1
DEFAULT_HEALTH_CHECK_INTERVAL = 60
DEFAULT_ENDPOINT_TIMEOUT = 5
DEFAULT_RECONNECT_DELAY = 1
DEFAULT_CONFIRMATION_TIMEOUT = 60
DEFAULT_COMPUTE_UNIT_PRICE = 1000

# Максимальна кількість спроб
MAX_RECONNECT_ATTEMPTS = 3

class ErrorCode(IntEnum):
    """Коди помилок"""
    UNKNOWN_ERROR = -1
    HTTP_ERROR = 1
    TIMEOUT = 2
    CLIENT_ERROR = 3
    RATE_LIMIT = 429
    SERVER_ERROR = 500
    MAX_RETRIES = 1000
    
class TransactionStatus(str, Enum):
    """Статуси транзакцій"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FINALIZED = "finalized"
    FAILED = "failed" 

class EndpointManager:
    def __init__(self):
        self.http_url = getenv('QUICKNODE_HTTP_URL')
        self.ws_url = getenv('QUICKNODE_WS_URL')
        
        if not self.http_url or not self.ws_url:
            raise ValueError("QUICKNODE_HTTP_URL та QUICKNODE_WS_URL повинні бути вказані в .env")
            
        self._endpoints = [self.http_url]
        self._ws_endpoints = [self.ws_url] 

        logger.info(f"Використовуємо HTTP URL: {self.http_url}")
        logger.info(f"Використовуємо WS URL: {self.ws_url}")

def validate_url(url: str, is_ws: bool = False) -> bool:
    if is_ws:
        pattern = r'^wss?:\/\/'
    else:
        pattern = r'^https?:\/\/'
    return bool(re.match(pattern, url)) 