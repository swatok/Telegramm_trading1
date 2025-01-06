"""
Модель для представлення котирувань від Jupiter API
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import List, Dict, Optional

@dataclass
class Quote:
    input_mint: str  # Вхідний токен
    output_mint: str  # Вихідний токен
    in_amount: Decimal  # Сума входу
    out_amount: Decimal  # Сума виходу
    price_impact: Decimal  # Вплив на ціну в %
    slippage: Decimal  # Допустимий slippage в %
    route_plan: List[dict]  # План маршруту
    other_amount_threshold: Decimal  # Мінімальна сума виходу
    swap_mode: str  # Режим свопу
    
    # Додаткова інформація
    fees: Optional[Dict[str, Decimal]] = None  # Комісії
    platform_fee: Optional[Decimal] = None  # Комісія платформи
    minimum_out_amount: Optional[Decimal] = None  # Мінімальна сума виходу з урахуванням slippage
    
    def __post_init__(self):
        """Валідація після створення"""
        if self.in_amount <= 0:
            raise ValueError("Сума входу повинна бути більше 0")
        if self.out_amount <= 0:
            raise ValueError("Сума виходу повинна бути більше 0")
            
    @property
    def price(self) -> Decimal:
        """Ціна токену"""
        return self.out_amount / self.in_amount if self.in_amount else Decimal("0")
        
    @property
    def total_fee_amount(self) -> Decimal:
        """Загальна сума комісій"""
        if not self.fees:
            return Decimal("0")
        return sum(self.fees.values())
        
    def to_dict(self) -> dict:
        """Конвертація в словник для збереження"""
        return {
            "input_mint": self.input_mint,
            "output_mint": self.output_mint,
            "in_amount": str(self.in_amount),
            "out_amount": str(self.out_amount),
            "price_impact": str(self.price_impact),
            "slippage": str(self.slippage),
            "route_plan": self.route_plan,
            "other_amount_threshold": str(self.other_amount_threshold),
            "swap_mode": self.swap_mode,
            "fees": {k: str(v) for k, v in self.fees.items()} if self.fees else None,
            "platform_fee": str(self.platform_fee) if self.platform_fee else None,
            "minimum_out_amount": str(self.minimum_out_amount) if self.minimum_out_amount else None
        }
        
    def __str__(self) -> str:
        """Рядкове представлення котирування"""
        return (
            f"Quote({self.input_mint[:4]}...→{self.output_mint[:4]}..., "
            f"in={float(self.in_amount):.4f}, out={float(self.out_amount):.4f}, "
            f"impact={float(self.price_impact):.2f}%)"
        ) 