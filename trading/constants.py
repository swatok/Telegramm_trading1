"""
Модуль з константами для торгової системи.
Містить всі необхідні константи та налаштування для торгових операцій.
"""

from decimal import Decimal
from typing import List, Dict
import os

# Токени
TOKEN_ADDRESS = "So11111111111111111111111111111111111111112"

# Баланси
BALANCE_MIN = Decimal("0.02")
TRANSACTION_MIN = Decimal("0.001")
POSITION_PERCENT = Decimal("5") / Decimal("100")

# Ліквідність та таймаути
LIQUIDITY_MIN = Decimal(os.getenv('MIN_LIQUIDITY_SOL', '40'))
CONFIRMATION_TIMEOUT = 60

# Take-profit налаштування
PROFIT_LEVELS = [
    {"level": Decimal("1"), "sell_percent": Decimal("20")},
    {"level": Decimal("2.5"), "sell_percent": Decimal("20")},
    {"level": Decimal("5"), "sell_percent": Decimal("20")},
    {"level": Decimal("10"), "sell_percent": Decimal("20")},
    {"level": Decimal("30"), "sell_percent": Decimal("25")},
    {"level": Decimal("90"), "sell_percent": Decimal("50")}
]

# Stop-loss налаштування
LOSS_LEVEL = Decimal("-0.75")  # -75%
