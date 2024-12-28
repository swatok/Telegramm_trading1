"""Trading monitor"""

import os
from loguru import logger
from typing import Optional, List
from datetime import datetime

from models.trade import Trade
from models.signal import Signal

class Monitor:
    """Клас для моніторингу торгових операцій"""
    def __init__(self):
        self.trades: List[Trade] = []
        self.signals: List[Signal] = []
        self.start_time = datetime.now()
        
    async def save_trade(self, trade: Trade):
        """Збереження торгової операції"""
        try:
            self.trades.append(trade)
            logger.info(f"Збережено торгову операцію: {trade}")
        except Exception as e:
            logger.error(f"Помилка збереження торгової операції: {str(e)}")
            
    async def update_trade(self, trade: Trade):
        """Оновлення торгової операції"""
        try:
            for i, t in enumerate(self.trades):
                if t.token_address == trade.token_address and t.timestamp == trade.timestamp:
                    self.trades[i] = trade
                    logger.info(f"Оновлено торгову операцію: {trade}")
                    return
        except Exception as e:
            logger.error(f"Помилка оновлення торгової операції: {str(e)}")
            
    async def save_signal(self, signal: Signal):
        """Збереження торгового сигналу"""
        try:
            self.signals.append(signal)
            logger.info(f"Збережено торговий сигнал: {signal}")
        except Exception as e:
            logger.error(f"Помилка збереження торгового сигналу: {str(e)}")
            
    async def update_signal(self, signal: Signal):
        """Оновлення торгового сигналу"""
        try:
            for i, s in enumerate(self.signals):
                if s.token_address == signal.token_address and s.timestamp == signal.timestamp:
                    self.signals[i] = signal
                    logger.info(f"Оновлено торговий сигнал: {signal}")
                    return
        except Exception as e:
            logger.error(f"Помилка оновлення торгового сигналу: {str(e)}")
            
    def get_stats(self) -> dict:
        """Отримання статистики"""
        try:
            total_trades = len(self.trades)
            completed_trades = len([t for t in self.trades if t.status == "completed"])
            failed_trades = len([t for t in self.trades if t.status == "failed"])
            pending_trades = len([t for t in self.trades if t.status == "pending"])
            
            total_signals = len(self.signals)
            processed_signals = len([s for s in self.signals if s.status != "pending"])
            
            return {
                "total_trades": total_trades,
                "completed_trades": completed_trades,
                "failed_trades": failed_trades,
                "pending_trades": pending_trades,
                "total_signals": total_signals,
                "processed_signals": processed_signals,
                "uptime": (datetime.now() - self.start_time).total_seconds()
            }
            
        except Exception as e:
            logger.error(f"Помилка отримання статистики: {str(e)}")
            return {} 