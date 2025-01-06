"""
Модель для представлення токену в мережі Solana
"""
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from typing import Optional, List

@dataclass
class Token:
    address: str  # Адреса токену в мережі Solana
    name: Optional[str] = None  # Назва токену
    symbol: Optional[str] = None  # Символ токену
    decimals: int = 9  # Кількість десяткових знаків (за замовчуванням 9 для SOL)
    
    # Ціни та ліквідність
    current_price_sol: Optional[Decimal] = None  # Поточна ціна в SOL
    current_price_usdc: Optional[Decimal] = None  # Поточна ціна в USDC
    liquidity_sol: Optional[Decimal] = None  # Ліквідність в SOL
    volume_24h: Optional[Decimal] = None  # Об'єм за 24 години
    
    # Метадані
    created_at: Optional[datetime] = None  # Час створення токену
    first_trade_at: Optional[datetime] = None  # Час першої торгівлі
    verified: bool = False  # Чи верифікований токен
    
    # Торгові параметри
    is_tradeable: bool = False  # Чи можна торгувати на Jupiter
    min_trade_size_sol: Decimal = Decimal("0.01")  # Мінімальний розмір торгівлі в SOL
    max_slippage: Decimal = Decimal("1.0")  # Максимальний допустимий slippage в %
    
    # Додаткова інформація
    website: Optional[str] = None  # Веб-сайт проекту
    twitter: Optional[str] = None  # Twitter проекту
    telegram: Optional[str] = None  # Telegram проекту
    holders_count: Optional[int] = None  # Кількість холдерів
    
    def __str__(self) -> str:
        """Рядкове представлення токену"""
        return f"{self.symbol or self.name or self.address[:8]}({self.address})"
        
    @property
    def short_address(self) -> str:
        """Скорочена адреса токену"""
        return f"{self.address[:4]}...{self.address[-4:]}"
        
    def to_dict(self) -> dict:
        """Конвертація в словник для збереження"""
        return {
            "address": self.address,
            "name": self.name,
            "symbol": self.symbol,
            "decimals": self.decimals,
            "current_price_sol": str(self.current_price_sol) if self.current_price_sol else None,
            "current_price_usdc": str(self.current_price_usdc) if self.current_price_usdc else None,
            "liquidity_sol": str(self.liquidity_sol) if self.liquidity_sol else None,
            "volume_24h": str(self.volume_24h) if self.volume_24h else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "first_trade_at": self.first_trade_at.isoformat() if self.first_trade_at else None,
            "verified": self.verified,
            "is_tradeable": self.is_tradeable,
            "min_trade_size_sol": str(self.min_trade_size_sol),
            "max_slippage": str(self.max_slippage),
            "website": self.website,
            "twitter": self.twitter,
            "telegram": self.telegram,
            "holders_count": self.holders_count
        } 