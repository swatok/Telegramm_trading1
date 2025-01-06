"""Фабрика репозиторіїв для централізованого управління"""

from typing import Optional
from utils import get_logger, singleton
from database import (
    ChannelRepository,
    PositionRepository,
    SignalRepository,
    TradeRepository,
    TransactionRepository,
    StatsRepository
)

logger = get_logger("repository_factory")

@singleton
class RepositoryFactory:
    """Клас для створення та управління репозиторіями"""
    
    def __init__(self, db_file: str = 'trading_bot.db'):
        """
        Ініціалізація фабрики репозиторіїв
        
        Args:
            db_file: Шлях до файлу бази даних
        """
        self.db_file = db_file
        self._channel_repo: Optional[ChannelRepository] = None
        self._position_repo: Optional[PositionRepository] = None
        self._signal_repo: Optional[SignalRepository] = None
        self._trade_repo: Optional[TradeRepository] = None
        self._transaction_repo: Optional[TransactionRepository] = None
        self._stats_repo: Optional[StatsRepository] = None
        
    @property
    def channel_repository(self) -> ChannelRepository:
        """Отримання репозиторію каналів"""
        if not self._channel_repo:
            self._channel_repo = ChannelRepository(self.db_file)
        return self._channel_repo
        
    @property
    def position_repository(self) -> PositionRepository:
        """Отримання репозиторію позицій"""
        if not self._position_repo:
            self._position_repo = PositionRepository(self.db_file)
        return self._position_repo
        
    @property
    def signal_repository(self) -> SignalRepository:
        """Отримання репозиторію сигналів"""
        if not self._signal_repo:
            self._signal_repo = SignalRepository(self.db_file)
        return self._signal_repo
        
    @property
    def trade_repository(self) -> TradeRepository:
        """Отримання репозиторію торгових операцій"""
        if not self._trade_repo:
            self._trade_repo = TradeRepository(self.db_file)
        return self._trade_repo
        
    @property
    def transaction_repository(self) -> TransactionRepository:
        """Отримання репозиторію транзакцій"""
        if not self._transaction_repo:
            self._transaction_repo = TransactionRepository(self.db_file)
        return self._transaction_repo
        
    @property
    def stats_repository(self) -> StatsRepository:
        """Отримання репозиторію статистики"""
        if not self._stats_repo:
            self._stats_repo = StatsRepository(self.db_file)
        return self._stats_repo
        
    def close_all(self):
        """Закриття всіх з'єднань з базою даних"""
        repos = [
            self._channel_repo,
            self._position_repo,
            self._signal_repo,
            self._trade_repo,
            self._transaction_repo,
            self._stats_repo
        ]
        
        for repo in repos:
            if repo:
                repo.close()
                
        logger.info("Всі з'єднання з базою даних закрито") 