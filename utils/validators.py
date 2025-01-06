from typing import Any, Optional, Dict
from decimal import Decimal
import re
from .logger import get_logger

logger = get_logger("validators")

def validate_decimal(value: Any, min_value: Optional[Decimal] = None, max_value: Optional[Decimal] = None) -> bool:
    """Валідація десяткового числа"""
    try:
        decimal_value = Decimal(str(value))
        if min_value is not None and decimal_value < min_value:
            return False
        if max_value is not None and decimal_value > max_value:
            return False
        return True
    except (TypeError, ValueError):
        return False

def validate_address(address: str) -> bool:
    """Валідація Solana адреси"""
    if not isinstance(address, str):
        return False
    # Базова перевірка формату Solana адреси
    pattern = r'^[1-9A-HJ-NP-Za-km-z]{32,44}$'
    return bool(re.match(pattern, address))

def validate_token_data(token_data: Dict[str, Any]) -> bool:
    """Валідація даних токена"""
    required_fields = ['address', 'symbol', 'decimals']
    
    # Перевірка наявності всіх обов'язкових полів
    if not all(field in token_data for field in required_fields):
        logger.error(f"Missing required fields in token data: {required_fields}")
        return False
    
    # Валідація адреси
    if not validate_address(token_data['address']):
        logger.error(f"Invalid token address: {token_data['address']}")
        return False
    
    # Валідація символу
    if not isinstance(token_data['symbol'], str) or len(token_data['symbol']) == 0:
        logger.error(f"Invalid token symbol: {token_data['symbol']}")
        return False
    
    # Валідація decimals
    try:
        decimals = int(token_data['decimals'])
        if not (0 <= decimals <= 18):
            logger.error(f"Invalid decimals value: {decimals}")
            return False
    except (ValueError, TypeError):
        logger.error(f"Invalid decimals format: {token_data['decimals']}")
        return False
    
    return True

def validate_price(price: Any) -> bool:
    """Валідація ціни"""
    try:
        price_decimal = Decimal(str(price))
        return price_decimal > Decimal('0')
    except (ValueError, TypeError, ArithmeticError):
        return False

def validate_percentage(value: Any, allow_zero: bool = False) -> bool:
    """Валідація процентного значення"""
    try:
        percentage = Decimal(str(value))
        if allow_zero:
            return Decimal('0') <= percentage <= Decimal('100')
        return Decimal('0') < percentage <= Decimal('100')
    except (ValueError, TypeError):
        return False

def validate_amount(amount: Any, min_amount: Optional[Decimal] = None) -> bool:
    """Валідація суми"""
    try:
        amount_decimal = Decimal(str(amount))
        if amount_decimal <= Decimal('0'):
            return False
        if min_amount is not None and amount_decimal < min_amount:
            return False
        return True
    except (ValueError, TypeError):
        return False
