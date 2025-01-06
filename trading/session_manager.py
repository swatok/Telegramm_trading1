"""
Модуль для управління торговими сесіями.
Відповідає за створення, відстеження та закриття торгових сесій.
"""

import uuid
from typing import Dict, Optional, List
from datetime import datetime
import asyncio
import aiohttp

from .performance_metrics import PerformanceMetrics
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class TradingSession:
    """Клас для представлення торгової сесії."""
    
    def __init__(self, session_id: str):
        """
        Ініціалізація торгової сесії.

        Args:
            session_id: Унікальний ідентифікатор сесії
        """
        self.session_id = session_id
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.is_active = True
        self.metrics = PerformanceMetrics()
        self.http_session: Optional[aiohttp.ClientSession] = None

class SessionManager:
    """
    Клас для управління торговими сесіями.
    Забезпечує створення та управління торговими сесіями.
    """

    def __init__(self):
        """Ініціалізація менеджера сесій."""
        self._sessions: Dict[str, TradingSession] = {}
        self._active_session: Optional[TradingSession] = None

    async def create_session(self) -> TradingSession:
        """
        Створення нової торгової сесії.

        Returns:
            Створена торгова сесія
        """
        session_id = str(uuid.uuid4())
        session = TradingSession(session_id)
        session.http_session = aiohttp.ClientSession()
        
        self._sessions[session_id] = session
        self._active_session = session
        
        logger.info(f"Створено нову торгову сесію: {session_id}")
        return session

    async def close_session(self, session_id: str):
        """
        Закриття торгової сесії.

        Args:
            session_id: Ідентифікатор сесії для закриття
        """
        if session_id in self._sessions:
            session = self._sessions[session_id]
            session.is_active = False
            session.end_time = datetime.now()
            
            if session.http_session and not session.http_session.closed:
                await session.http_session.close()
            
            if self._active_session and self._active_session.session_id == session_id:
                self._active_session = None
            
            logger.info(f"Закрито торгову сесію: {session_id}")

    async def close_all_sessions(self):
        """Закриття всіх активних сесій."""
        for session_id in list(self._sessions.keys()):
            await self.close_session(session_id)
        logger.info("Всі торгові сесії закрито")

    def get_session(self, session_id: str) -> Optional[TradingSession]:
        """
        Отримання сесії за ідентифікатором.

        Args:
            session_id: Ідентифікатор сесії

        Returns:
            Торгова сесія або None
        """
        return self._sessions.get(session_id)

    def get_active_session(self) -> Optional[TradingSession]:
        """
        Отримання активної сесії.

        Returns:
            Активна торгова сесія або None
        """
        return self._active_session

    def get_all_sessions(self) -> List[TradingSession]:
        """
        Отримання всіх сесій.

        Returns:
            Список всіх сесій
        """
        return list(self._sessions.values())

    def get_session_stats(self, session_id: str) -> Optional[Dict]:
        """
        Отримання статистики сесії.

        Args:
            session_id: Ідентифікатор сесії

        Returns:
            Словник зі статистикою сесії або None
        """
        session = self.get_session(session_id)
        if not session:
            return None

        duration = (
            session.end_time - session.start_time
            if session.end_time
            else datetime.now() - session.start_time
        )

        return {
            'session_id': session.session_id,
            'start_time': session.start_time.isoformat(),
            'end_time': session.end_time.isoformat() if session.end_time else None,
            'duration': str(duration),
            'is_active': session.is_active,
            'metrics': session.metrics.get_performance_summary()
        }

    async def cleanup_old_sessions(self, max_age_hours: int = 24):
        """
        Очищення старих сесій.

        Args:
            max_age_hours: Максимальний вік сесій в годинах
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        for session_id, session in list(self._sessions.items()):
            if not session.is_active and session.end_time < cutoff_time:
                await self.close_session(session_id)
                self._sessions.pop(session_id)
                
        logger.info(f"Очищено сесії старіші за {max_age_hours} годин")

    async def __aenter__(self):
        """Створення сесії при вході в контекст."""
        if not self._active_session:
            await self.create_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закриття сесій при виході з контексту."""
        await self.close_all_sessions() 