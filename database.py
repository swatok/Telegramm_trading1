"""
Модуль для роботи з базою даних
"""

import sqlite3
import logging
from datetime import datetime
import time
from typing import List, Dict, Optional
import json
from loguru import logger

class Database:
    def __init__(self):
        """Ініціалізація з'єднання з базою даних"""
        try:
            self.db_file = 'trading_bot.db'
            self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
            logger.info("З'єднання з базою даних встановлено")
            self._create_tables()
        except Exception as e:
            logger.error(f"Помилка ініціалізації бази даних: {e}")
            raise
            
    def _execute_with_retry(self, query: str, params: tuple = None, max_retries: int = 3, retry_delay: int = 1):
        """Виконання SQL-запиту з повторними спробами"""
        for attempt in range(max_retries):
            try:
                if not self.conn or not self.cursor:
                    self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
                    self.conn.row_factory = sqlite3.Row
                    self.cursor = self.conn.cursor()
                    
                if params:
                    self.cursor.execute(query, params)
                else:
                    self.cursor.execute(query)
                    
                self.conn.commit()
                return True
            except sqlite3.Error as e:
                logger.error(f"Помилка виконання запиту (спроба {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                raise

    def _create_tables(self):
        """Створення таблиць бази даних"""
        try:
            # Таблиця каналів
            self._execute_with_retry('''
                CREATE TABLE IF NOT EXISTS channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    settings TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблиця сигналів
            self._execute_with_retry('''
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    token_address TEXT NOT NULL,
                    token_name TEXT,
                    signal_type TEXT,
                    price REAL,
                    amount REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(message_id, channel_id)
                )
            ''')
            
            # Таблиця транзакцій
            self._execute_with_retry('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signature TEXT UNIQUE NOT NULL,
                    token_address TEXT NOT NULL,
                    amount REAL NOT NULL,
                    type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    balance_change REAL,
                    confirmations INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблиця позицій
            self._execute_with_retry('''
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token_address TEXT NOT NULL,
                    token_symbol TEXT,
                    entry_price REAL NOT NULL,
                    current_price REAL,
                    amount REAL NOT NULL,
                    remaining_amount REAL NOT NULL,
                    status TEXT NOT NULL,
                    transaction_signature TEXT,
                    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP,
                    FOREIGN KEY(transaction_signature) REFERENCES transactions(signature)
                )
            ''')
            
            # Таблиця торгів
            self._execute_with_retry('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token_address TEXT NOT NULL,
                    token_name TEXT,
                    entry_price REAL NOT NULL,
                    exit_price REAL,
                    amount REAL NOT NULL,
                    type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    pnl REAL,
                    position_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(position_id) REFERENCES positions(id)
                )
            ''')
            
            # Таблиця логів
            self._execute_with_retry('''
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    details TEXT,
                    session_id TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблиця метрик продуктивності
            self._execute_with_retry('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    api_calls INTEGER DEFAULT 0,
                    successful_trades INTEGER DEFAULT 0,
                    failed_trades INTEGER DEFAULT 0,
                    average_response_time REAL DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблиця інформації про токени
            self._execute_with_retry('''
                CREATE TABLE IF NOT EXISTS token_info (
                    address TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    decimals INTEGER DEFAULT 9,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблиця для балансів
            self._execute_with_retry('''
                CREATE TABLE IF NOT EXISTS balances (
                    token_address TEXT PRIMARY KEY,
                    amount REAL DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблиця налаштувань
            self._execute_with_retry('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            
            # Додаємо значення за замовчуванням для налаштувань
            default_settings = {
                'min_sol_balance': '0.02',
                'position_size': '5',
                'max_slippage': '1',
                'tp_1_percent': '20',
                'tp_2_percent': '20',
                'tp_3_percent': '20',
                'stop_loss_level': '-75'
            }
            
            for key, value in default_settings.items():
                self._execute_with_retry(
                    "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                    (key, value)
                )
            
            self.conn.commit()
            logger.info("Таблиці успішно створені")
            return True
            
        except Exception as e:
            logger.error(f"Помилка створення таблиць: {e}")
            return False

    def add_trade(self, trade: Dict) -> bool:
        """Додавання торгової операції"""
        try:
            self._execute_with_retry('''
                INSERT INTO trades (
                    token_address, token_name, entry_price,
                    exit_price, amount, type, status,
                    pnl, position_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade['token_address'],
                trade['token_name'],
                trade['entry_price'],
                trade.get('exit_price'),
                trade['amount'],
                trade['type'],
                trade.get('status', 'open'),
                trade.get('pnl', 0),
                trade.get('position_id')
            ))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Помилка додавання торгової операції: {e}")
            return False

    def update_trade(self, trade_id: int, updates: Dict) -> bool:
        """Оновлення торгової операції"""
        try:
            update_fields = []
            values = []
            for key, value in updates.items():
                update_fields.append(f"{key} = ?")
                values.append(value)
            values.append(trade_id)
            
            query = f'''
                UPDATE trades
                SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            '''
            
            self._execute_with_retry(query, tuple(values))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Помилка оновлення торгової операції: {e}")
            return False
            
    def get_trade(self, trade_id: int) -> Optional[Dict]:
        """Отримання торгової операції за ID"""
        try:
            self._execute_with_retry('''
                SELECT * FROM trades
                WHERE id = ?
            ''', (trade_id,))
            
            result = self.cursor.fetchone()
            if result:
                columns = [description[0] for description in self.cursor.description]
                return dict(zip(columns, result))
            return None
        except Exception as e:
            logger.error(f"Помилка отримання торгової операції: {e}")
            return None
            
    def get_trades_by_position(self, position_id: int) -> List[Dict]:
        """Отримання торгових операцій для позиції"""
        try:
            self._execute_with_retry('''
                SELECT * FROM trades
                WHERE position_id = ?
                ORDER BY created_at DESC
            ''', (position_id,))
            
            columns = [description[0] for description in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"Помилка отримання торгових операцій: {e}")
            return []
            
    def get_trades_by_token(self, token_address: str) -> List[Dict]:
        """Отримання торгових операцій для токена"""
        try:
            self._execute_with_retry('''
                SELECT * FROM trades
                WHERE token_address = ?
                ORDER BY created_at DESC
            ''', (token_address,))
            
            columns = [description[0] for description in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"Помилка отримання торгових операцій: {e}")
            return []
            
    def get_trades_in_time_range(self, start_time: datetime, end_time: datetime) -> List[Dict]:
        """Отримання торгових операцій за період часу"""
        try:
            self._execute_with_retry('''
                SELECT * FROM trades
                WHERE created_at BETWEEN ? AND ?
                ORDER BY created_at DESC
            ''', (start_time, end_time))
            
            columns = [description[0] for description in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"Помилка отримання торгових операцій: {e}")
            return []
            
    def calculate_pnl(self, position_id: int) -> float:
        """Розрахунок PnL для позиції"""
        try:
            self._execute_with_retry('''
                SELECT 
                    SUM(CASE 
                        WHEN type = 'buy' THEN -amount * entry_price
                        WHEN type = 'sell' THEN amount * exit_price
                        ELSE 0
                    END) as pnl
                FROM trades
                WHERE position_id = ? AND status = 'closed'
            ''', (position_id,))
            
            result = self.cursor.fetchone()
            return result[0] if result and result[0] is not None else 0
        except Exception as e:
            logger.error(f"Помилка розрахунку PnL: {e}")
            return 0

    def get_trading_stats(self, period: str = 'all') -> Dict:
        """Отримання торгової статистики"""
        try:
            if period == 'all':
                self.cursor.execute('''
                    SELECT COUNT(*) as total_trades,
                           SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as profitable_trades,
                           SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as unprofitable_trades,
                           SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate,
                           SUM(pnl) as total_profit,
                           MAX(CASE WHEN pnl > 0 THEN pnl ELSE 0 END) as largest_win,
                           MIN(CASE WHEN pnl < 0 THEN pnl ELSE 0 END) as largest_loss,
                           AVG(pnl) as avg_profit,
                           COUNT(DISTINCT token_address) as traded_tokens,
                           SUM(pnl) as total_pnl
                    FROM trades
                    WHERE status = 'closed'
                ''')
            else:
                # Додат�� фільтрацію за періодом
                self.cursor.execute('''
                    SELECT COUNT(*) as total_trades,
                           SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as profitable_trades,
                           SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as unprofitable_trades,
                           SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate,
                           SUM(pnl) as total_profit,
                           MAX(CASE WHEN pnl > 0 THEN pnl ELSE 0 END) as largest_win,
                           MIN(CASE WHEN pnl < 0 THEN pnl ELSE 0 END) as largest_loss,
                           AVG(pnl) as avg_profit,
                           COUNT(DISTINCT token_address) as traded_tokens,
                           SUM(pnl) as total_pnl
                    FROM trades
                    WHERE status = 'closed'
                    AND created_at >= datetime('now', ?)
                ''', (f'-{period}',))
            
            row = self.cursor.fetchone()
            if not row:
                return {
                    'total_trades': 0,
                    'profitable_trades': 0,
                    'unprofitable_trades': 0,
                    'win_rate': 0,
                    'total_profit': 0,
                    'largest_win': 0,
                    'largest_loss': 0,
                    'avg_profit': 0,
                    'traded_tokens': 0,
                    'total_pnl': 0
                }
            
            return {
                'total_trades': row[0] or 0,
                'profitable_trades': row[1] or 0,
                'unprofitable_trades': row[2] or 0,
                'win_rate': row[3] or 0,
                'total_profit': row[4] or 0,
                'largest_win': row[5] or 0,
                'largest_loss': row[6] or 0,
                'avg_profit': row[7] or 0,
                'traded_tokens': row[8] or 0,
                'total_pnl': row[9] or 0
            }
            
        except Exception as e:
            logger.error(f"Помилка отримання торгової статистики: {e}")
            return {
                'total_trades': 0,
                'profitable_trades': 0,
                'unprofitable_trades': 0,
                'win_rate': 0,
                'total_profit': 0,
                'largest_win': 0,
                'largest_loss': 0,
                'avg_profit': 0,
                'traded_tokens': 0,
                'total_pnl': 0
            }

    def get_token_stats(self, token_address: str) -> Optional[Dict]:
        """Отримання статистики для конкретного токена"""
        try:
            self._execute_with_retry('''
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as profitable_trades,
                    SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as unprofitable_trades,
                    SUM(pnl) as total_pnl,
                    MAX(pnl) as max_profit,
                    MIN(pnl) as max_loss,
                    AVG(pnl) as avg_pnl,
                    SUM(amount) as total_volume,
                    MIN(entry_price) as min_price,
                    MAX(entry_price) as max_price,
                    AVG(entry_price) as avg_price
                FROM trades
                WHERE token_address = ?
                    AND status = 'closed'
            ''', (token_address,))
            
            result = self.cursor.fetchone()
            if result:
                columns = [description[0] for description in self.cursor.description]
                stats = dict(zip(columns, result))
                
                # Додаткові розрахунки
                if stats['total_trades'] > 0:
                    stats['win_rate'] = (stats['profitable_trades'] / stats['total_trades']) * 100
                else:
                    stats['win_rate'] = 0
                    
                return stats
            return None
        except Exception as e:
            logger.error(f"Помилка отримання статистики токена: {e}")
            return None

    def add_signal(self, signal: Dict) -> bool:
        """Додавання торгового сигналу"""
        try:
            self._execute_with_retry('''
                INSERT INTO signals (
                    message_id, channel_id, token_address,
                    token_name, signal_type, price, amount
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                signal['message_id'],
                signal['channel_id'],
                signal['token_address'],
                signal['token_name'],
                signal['signal_type'],
                signal.get('price', 0),
                signal.get('amount', 0)
            ))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Помилка додавання сигналу: {e}")
            return False

    def get_signal(self, message_id: int, channel_id: int) -> Optional[Dict]:
        """Отримання сигналу за ID повідомлення та каналу"""
        try:
            self._execute_with_retry('''
                SELECT * FROM signals 
                WHERE message_id = ? AND channel_id = ?
            ''', (message_id, channel_id))
            
            result = self.cursor.fetchone()
            if result:
                columns = [description[0] for description in self.cursor.description]
                return dict(zip(columns, result))
            return None
        except Exception as e:
            logger.error(f"Помилка отримання сигналу: {e}")
            return None

    def get_signals_by_channel(self, channel_id: int, limit: int = 100) -> List[Dict]:
        """Отримання сигналів для каналу"""
        try:
            self._execute_with_retry('''
                SELECT * FROM signals
                WHERE channel_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (channel_id, limit))
            
            columns = [description[0] for description in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"Помилка отримання сигналів: {e}")
            return []

    def get_signals_by_token(self, token_address: str, limit: int = 100) -> List[Dict]:
        """Отримання сигналів для токена"""
        try:
            self._execute_with_retry('''
                SELECT * FROM signals
                WHERE token_address = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (token_address, limit))
            
            columns = [description[0] for description in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"Помилка отримання сигналів: {e}")
            return []

    def get_recent_signals(self, limit: int = 100) -> List[Dict]:
        """Отримання останніх сигналів"""
        try:
            self._execute_with_retry('''
                SELECT * FROM signals
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            columns = [description[0] for description in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"Помилка отримання сигналів: {e}")
            return []

    def add_transaction(self, transaction: Dict) -> bool:
        """Додавання транзакції"""
        try:
            self._execute_with_retry('''
                INSERT INTO transactions (
                    signature, token_address, amount, type,
                    status, confirmations, balance_change
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                transaction['signature'],
                transaction['token_address'],
                transaction['amount'],
                transaction['type'],
                transaction.get('status', 'pending'),
                transaction.get('confirmations', 0),
                transaction.get('balance_change', 0)
            ))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Помилка додавання транзакції: {e}")
            return False

    def update_transaction(self, signature: str, updates: Dict) -> bool:
        """Оновлення транзакції"""
        try:
            update_fields = []
            values = []
            for key, value in updates.items():
                update_fields.append(f"{key} = ?")
                values.append(value)
            values.append(signature)
            
            query = f'''
                UPDATE transactions
                SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                WHERE signature = ?
            '''
            
            self._execute_with_retry(query, tuple(values))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Помилка оновлення транзакції: {e}")
            return False

    def get_transaction(self, signature: str) -> Optional[Dict]:
        """Отримання транзакції за підписом"""
        try:
            self._execute_with_retry('''
                SELECT * FROM transactions
                WHERE signature = ?
            ''', (signature,))
            
            result = self.cursor.fetchone()
            if result:
                columns = [description[0] for description in self.cursor.description]
                return dict(zip(columns, result))
            return None
        except Exception as e:
            logger.error(f"Помилка отримання транзакції: {e}")
            return None

    def get_transactions_by_token(self, token_address: str) -> List[Dict]:
        """Отримання транзакцій для токена"""
        try:
            self._execute_with_retry('''
                SELECT * FROM transactions
                WHERE token_address = ?
                ORDER BY created_at DESC
            ''', (token_address,))
            
            columns = [description[0] for description in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"Помилка отримання транзакцій: {e}")
            return []

    def get_transactions_by_status(self, status: str) -> List[Dict]:
        """Отримання транзакцій за статусом"""
        try:
            self._execute_with_retry('''
                SELECT * FROM transactions
                WHERE status = ?
                ORDER BY created_at DESC
            ''', (status,))
            
            columns = [description[0] for description in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"Помилка отримання транзакцій: {e}")
            return []

    def get_recent_transactions(self, limit: int = 100) -> List[Dict]:
        """Отримання останніх транзакцій"""
        try:
            self._execute_with_retry('''
                SELECT * FROM transactions
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
            
            columns = [description[0] for description in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"Помилка отримання транзакцій: {e}")
            return []

    def get_transactions_in_time_range(self, start_time: datetime, end_time: datetime) -> List[Dict]:
        """Отриман��я транзакцій за період часу"""
        try:
            self._execute_with_retry('''
                SELECT * FROM transactions
                WHERE created_at BETWEEN ? AND ?
                ORDER BY created_at DESC
            ''', (start_time, end_time))
            
            columns = [description[0] for description in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"Помилка отримання транзакцій: {e}")
            return []

    def delete_old_transactions(self, days: int = 30) -> bool:
        """Видалення старих транзакцій"""
        try:
            self._execute_with_retry('''
                DELETE FROM transactions
                WHERE created_at < datetime('now', '-? days')
            ''', (days,))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Помилка видалення старих транзакцій: {e}")
            return False

    def get_signals_in_time_range(self, start_time: datetime, end_time: datetime) -> List[Dict]:
        """Отримання сигналів за період"""
        try:
            self.cursor.execute('''
                SELECT id, message_id, channel_id, token_address, token_name,
                       signal_type, price, amount, created_at
                FROM signals
                WHERE created_at BETWEEN ? AND ?
                ORDER BY created_at DESC
            ''', (start_time, end_time))
            
            rows = self.cursor.fetchall()
            signals = []
            for row in rows:
                signal = {
                    'id': row[0],
                    'message_id': row[1],
                    'channel_id': row[2],
                    'token_address': row[3],
                    'token_name': row[4],
                    'signal_type': row[5],
                    'price': row[6],
                    'amount': row[7],
                    'created_at': row[8]
                }
                signals.append(signal)
                
            return signals
            
        except Exception as e:
            logger.error(f"Помилка отримання сигналів за період: {e}")
            return []

    def add_position(self, position: Dict) -> Optional[int]:
        """Додавання нової позиції"""
        try:
            self._execute_with_retry('''
                INSERT INTO positions (
                    token_address, token_symbol, entry_price,
                    current_price, amount, remaining_amount,
                    status, transaction_signature
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                position['token_address'],
                position['token_symbol'],
                position['entry_price'],
                position.get('current_price', position['entry_price']),
                position['amount'],
                position['remaining_amount'],
                position.get('status', 'open'),
                position.get('transaction_signature')
            ))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            logger.error(f"Помилка додавання позиції: {e}")
            return None

    def update_position(self, position_id: int, updates: Dict) -> bool:
        """Оновлення позиції"""
        try:
            update_fields = []
            values = []
            for key, value in updates.items():
                update_fields.append(f"{key} = ?")
                values.append(value)
            values.append(position_id)
            
            query = f'''
                UPDATE positions
                SET {', '.join(update_fields)}
                WHERE id = ?
            '''
            
            self._execute_with_retry(query, tuple(values))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Помилка оновлення позиції: {e}")
            return False

    def get_position(self, position_id: int) -> Optional[Dict]:
        """Отримання позиції за ID"""
        try:
            self._execute_with_retry('''
                SELECT * FROM positions
                WHERE id = ?
            ''', (position_id,))
            
            result = self.cursor.fetchone()
            if result:
                columns = [description[0] for description in self.cursor.description]
                return dict(zip(columns, result))
            return None
        except Exception as e:
            logger.error(f"Помилка отримання позиції: {e}")
            return None
            
    def get_positions_by_token(self, token_address: str) -> List[Dict]:
        """Отримання позицій для токена"""
        try:
            self._execute_with_retry('''
                SELECT * FROM positions
                WHERE token_address = ?
                ORDER BY opened_at DESC
            ''', (token_address,))
            
            columns = [description[0] for description in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"Помилка отримання позицій: {e}")
            return []

    def get_open_positions(self) -> List[Dict]:
        """Отримання відкритих позицій"""
        try:
            self._execute_with_retry('''
                SELECT * FROM positions
                WHERE status = 'open'
                ORDER BY opened_at DESC
            ''')
            
            columns = [description[0] for description in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"Помилка отримання відкритих позицій: {e}")
            return []

    def get_closed_positions(self, limit: int = 100) -> List[Dict]:
        """Отримання закритих позицій"""
        try:
            self._execute_with_retry('''
                SELECT * FROM positions
                WHERE status = 'closed'
                ORDER BY closed_at DESC
                LIMIT ?
            ''', (limit,))
            
            columns = [description[0] for description in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"Помилка отримання закритих позицій: {e}")
            return []

    def get_positions_in_time_range(self, start_time: datetime, end_time: datetime) -> List[Dict]:
        """Отримання позицій за період часу"""
        try:
            self._execute_with_retry('''
                SELECT * FROM positions
                WHERE opened_at BETWEEN ? AND ?
                ORDER BY opened_at DESC
            ''', (start_time, end_time))
            
            columns = [description[0] for description in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"Помилка отримання позицій за період: {e}")
            return []

    def calculate_position_pnl(self, position_id: int) -> Optional[float]:
        """Розрахунок PnL для позиції"""
        try:
            position = self.get_position(position_id)
            if not position:
                return None
                
            trades = self.get_trades_by_position(position_id)
            
            total_cost = 0
            total_proceeds = 0
            
            for trade in trades:
                if trade['type'] == 'buy':
                    total_cost += trade['amount'] * trade['entry_price']
                elif trade['type'] == 'sell':
                    total_proceeds += trade['amount'] * trade['exit_price']
                    
            return total_proceeds - total_cost
            
        except Exception as e:
            logger.error(f"Помилка розрахунку PnL для позиції: {e}")
            return None

    def update_position_prices(self, positions: List[Dict]) -> bool:
        """Масове оновлення цін позицій"""
        try:
            for position in positions:
                self.update_position(position['id'], {
                    'current_price': position['current_price'],
                    'pnl': position.get('pnl', 0)
                })
            return True
        except Exception as e:
            logger.error(f"Помилка оновлення цін позицій: {e}")
            return False
            
    def update_balance(self, token_address: str, updates: Dict) -> bool:
        """Оновлення балансу токена"""
        try:
            self._execute_with_retry('''
                INSERT INTO balances (token_address, amount, last_updated)
                VALUES (?, ?, ?)
                ON CONFLICT(token_address) DO UPDATE SET
                    amount = ?,
                    last_updated = ?
            ''', (
                token_address,
                updates['amount'],
                updates['last_updated'],
                updates['amount'],
                updates['last_updated']
            ))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Помилка оновлення балансу: {e}")
            return False
            
    def get_balance(self, token_address: str) -> Optional[Dict]:
        """Отримання балансу токена"""
        try:
            self._execute_with_retry('''
                SELECT * FROM balances
                WHERE token_address = ?
            ''', (token_address,))
            
            result = self.cursor.fetchone()
            if result:
                columns = [description[0] for description in self.cursor.description]
                return dict(zip(columns, result))
            return None
        except Exception as e:
            logger.error(f"Помилка отримання балансу: {e}")
            return None
            
    def get_all_balances(self) -> List[Dict]:
        """Отримання всіх балансів"""
        try:
            self._execute_with_retry('''
                SELECT * FROM balances
                ORDER BY last_updated DESC
            ''')
            
            columns = [description[0] for description in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"Помилка отримання балансів: {e}")
            return []
            
    def delete_balance(self, token_address: str) -> bool:
        """Видалення балансу токена"""
        try:
            self._execute_with_retry('''
                DELETE FROM balances
                WHERE token_address = ?
            ''', (token_address,))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Помилка видалення балансу: {e}")
            return False
            
    def add_session(self, session: Dict) -> bool:
        """Додавання нової сесії"""
        try:
            self._execute_with_retry('''
                INSERT INTO sessions (
                    id, start_time, status,
                    processed_signals, successful_trades,
                    failed_trades, total_volume
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                session['id'],
                session['start_time'],
                session.get('status', 'active'),
                session.get('processed_signals', 0),
                session.get('successful_trades', 0),
                session.get('failed_trades', 0),
                session.get('total_volume', 0)
            ))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Помилка додавання сесії: {e}")
            return False
            
    def update_session(self, session_id: str, updates: Dict) -> bool:
        """Оновлення сесії"""
        try:
            update_fields = []
            values = []
            for key, value in updates.items():
                update_fields.append(f"{key} = ?")
                values.append(value)
            values.append(session_id)
            
            query = f'''
                UPDATE sessions
                SET {', '.join(update_fields)}
                WHERE id = ?
            '''
            
            self._execute_with_retry(query, tuple(values))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Помилка оновлення сесії: {e}")
            return False
            
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Отримання сесії за ID"""
        try:
            self._execute_with_retry('''
                SELECT * FROM sessions
                WHERE id = ?
            ''', (session_id,))
            
            result = self.cursor.fetchone()
            if result:
                columns = [description[0] for description in self.cursor.description]
                return dict(zip(columns, result))
            return None
        except Exception as e:
            logger.error(f"Помилка отримання сесії: {e}")
            return None
            
    def get_active_session(self) -> Optional[Dict]:
        """Отримання активної сесії"""
        try:
            self._execute_with_retry('''
                SELECT * FROM sessions
                WHERE status = 'active'
                ORDER BY start_time DESC
                LIMIT 1
            ''')
            
            result = self.cursor.fetchone()
            if result:
                columns = [description[0] for description in self.cursor.description]
                return dict(zip(columns, result))
            return None
        except Exception as e:
            logger.error(f"Помилка отримання активної сесії: {e}")
            return None
            
    def get_recent_sessions(self, limit: int = 10) -> List[Dict]:
        """Отримання останніх сесій"""
        try:
            self._execute_with_retry('''
                SELECT * FROM sessions
                ORDER BY start_time DESC
                LIMIT ?
            ''', (limit,))
            
            columns = [description[0] for description in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"Помилка отримання останніх сесій: {e}")
            return []
            
    def update_performance_metrics(self, session_id: str, metrics: Dict) -> bool:
        """Оновлення метрик продуктивності"""
        try:
            self._execute_with_retry('''
                INSERT INTO performance_metrics (
                    session_id, timestamp, api_calls,
                    successful_trades, failed_trades,
                    average_response_time
                )
                VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, ?)
            ''', (
                session_id,
                metrics.get('api_calls', 0),
                metrics.get('successful_trades', 0),
                metrics.get('failed_trades', 0),
                metrics.get('average_response_time', 0)
            ))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Помилка оновлення метрик: {e}")
            return False
            
    def get_performance_metrics(self, session_id: str) -> List[Dict]:
        """Отримання метрик продуктивності для сесії"""
        try:
            self._execute_with_retry('''
                SELECT * FROM performance_metrics
                WHERE session_id = ?
                ORDER BY timestamp DESC
            ''', (session_id,))
            
            columns = [description[0] for description in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"Помилка отримання метрик: {e}")
            return []
            
    def add_log(self, log: Dict) -> bool:
        """Додавання логу"""
        try:
            self._execute_with_retry('''
                INSERT INTO logs (
                    level, message, details,
                    session_id
                )
                VALUES (?, ?, ?, ?)
            ''', (
                log['level'],
                log['message'],
                log.get('details'),
                log.get('session_id')
            ))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Помилка додавання логу: {e}")
            return False
            
    def get_logs(self, session_id: str = None, limit: int = 100) -> List[Dict]:
        """Отримання логів"""
        try:
            if session_id:
                self._execute_with_retry('''
                    SELECT * FROM logs
                    WHERE session_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (session_id, limit))
            else:
                self._execute_with_retry('''
                    SELECT * FROM logs
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))
            
            columns = [description[0] for description in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"Помилка отримання логів: {e}")
            return []
            
    def add_channel(self, channel: Dict) -> bool:
        """Додавання нового каналу"""
        try:
            # Спочатку перевіряємо чи канал вже існує
            self._execute_with_retry(
                "SELECT name FROM channels WHERE name = ?",
                (channel['name'],)
            )
            existing = self.cursor.fetchone()
            
            if existing:
                # Оновлюємо існуючий канал
                self._execute_with_retry('''
                    UPDATE channels 
                    SET type = ?, status = ?, settings = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE name = ?
                ''', (
                    channel.get('type', 'trading'),
                    channel.get('status', 'active'),
                    json.dumps(channel.get('settings', {})),
                    channel['name']
                ))
            else:
                # Додаємо новий канал
                self._execute_with_retry('''
                    INSERT INTO channels (
                        name, type, status, settings
                    )
                    VALUES (?, ?, ?, ?)
                ''', (
                    channel['name'],
                    channel.get('type', 'trading'),
                    channel.get('status', 'active'),
                    json.dumps(channel.get('settings', {}))
                ))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Помилка додавання каналу: {e}")
            return False
            
    def update_channel(self, channel_id: int, updates: Dict) -> bool:
        """Оновлення каналу"""
        try:
            update_fields = []
            values = []
            for key, value in updates.items():
                if key == 'settings':
                    value = json.dumps(value)
                update_fields.append(f"{key} = ?")
                values.append(value)
            values.append(channel_id)
            
            query = f'''
                UPDATE channels
                SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            '''
            
            self._execute_with_retry(query, tuple(values))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Помилка оновлення каналу: {e}")
            return False
            
    def get_channel(self, channel_id: int) -> Optional[Dict]:
        """Отримання каналу за ID"""
        try:
            self._execute_with_retry('''
                SELECT * FROM channels
                WHERE id = ?
            ''', (channel_id,))
            
            result = self.cursor.fetchone()
            if result:
                columns = [description[0] for description in self.cursor.description]
                channel = dict(zip(columns, result))
                channel['settings'] = json.loads(channel['settings'])
                return channel
            return None
        except Exception as e:
            logger.error(f"Помилка отримання каналу: {e}")
            return None
            
    def get_channel_by_name(self, channel_name: str) -> Optional[Dict]:
        """Отримання каналу за назвою"""
        try:
            self._execute_with_retry('''
                SELECT id, name, type, status, settings
                FROM channels
                WHERE name = ?
            ''', (channel_name,))
            
            result = self.cursor.fetchone()
            if result:
                return {
                    'id': result[0],
                    'name': result[1],
                    'type': result[2],
                    'status': result[3],
                    'settings': json.loads(result[4]) if result[4] else {}
                }
            return None
            
        except Exception as e:
            logger.error(f"Помилка отримання каналу за назвою: {e}")
            return None
            
    def get_active_channels(self) -> List[Dict]:
        """Отримання активних каналів"""
        try:
            self._execute_with_retry('''
                SELECT * FROM channels
                WHERE status = 'active'
                ORDER BY created_at DESC
            ''')
            
            columns = [description[0] for description in self.cursor.description]
            channels = []
            for row in self.cursor.fetchall():
                channel = dict(zip(columns, row))
                channel['settings'] = json.loads(channel['settings'])
                channels.append(channel)
            return channels
        except Exception as e:
            logger.error(f"Помилка отримання активних каналів: {e}")
            return []
            
    def get_all_channels(self) -> List[Dict]:
        """Отримання всіх каналів"""
        try:
            self._execute_with_retry('''
                SELECT * FROM channels
                ORDER BY created_at DESC
            ''')
            
            columns = [description[0] for description in self.cursor.description]
            channels = []
            for row in self.cursor.fetchall():
                channel = dict(zip(columns, row))
                channel['settings'] = json.loads(channel['settings'])
                channels.append(channel)
            return channels
        except Exception as e:
            logger.error(f"Помилка отримання каналів: {e}")
            return []
            
    def delete_channel(self, channel_id: int) -> bool:
        """Видалення каналу"""
        try:
            self._execute_with_retry('''
                DELETE FROM channels
                WHERE id = ?
            ''', (channel_id,))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Помилка видалення каналу: {e}")
            return False
            
    def close(self):
        """Закриття з'єднання з базою даних"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def add_order(self, order: Dict) -> Optional[int]:
        """Додавання нового ордера"""
        try:
            self._execute_with_retry('''
                INSERT INTO orders (
                    position_id, type, price,
                    amount, status
                )
                VALUES (?, ?, ?, ?, ?)
            ''', (
                order['position_id'],
                order['type'],
                order['price'],
                order['amount'],
                order.get('status', 'active')
            ))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            logger.error(f"Помилка додавання ордера: {e}")
            return None
            
    def update_order(self, order_id: int, updates: Dict) -> bool:
        """Оновлення ордера"""
        try:
            update_fields = []
            values = []
            for key, value in updates.items():
                update_fields.append(f"{key} = ?")
                values.append(value)
            values.append(order_id)
            
            query = f'''
                UPDATE orders
                SET {', '.join(update_fields)}
                WHERE id = ?
            '''
            
            self._execute_with_retry(query, tuple(values))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Помилка оновлення ордера: {e}")
            return False
            
    def get_order(self, order_id: int) -> Optional[Dict]:
        """Отримання ордера за ID"""
        try:
            self._execute_with_retry('''
                SELECT * FROM orders
                WHERE id = ?
            ''', (order_id,))
            
            result = self.cursor.fetchone()
            if result:
                columns = [description[0] for description in self.cursor.description]
                return dict(zip(columns, result))
            return None
        except Exception as e:
            logger.error(f"Помилка отримання ордера: {e}")
            return None
            
    def get_orders_by_position(self, position_id: int) -> List[Dict]:
        """Отримання ордерів для позиції"""
        try:
            self._execute_with_retry('''
                SELECT * FROM orders
                WHERE position_id = ?
                ORDER BY created_at DESC
            ''', (position_id,))
            
            columns = [description[0] for description in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"Помилка отримання ордерів: {e}")
            return []
            
    def get_active_orders(self) -> List[Dict]:
        """Отримання активних ордерів"""
        try:
            self.cursor.execute('''
                SELECT o.id, o.position_id, o.type, o.price, o.amount, o.status,
                       o.created_at, o.executed_at, p.token_address, p.token_symbol
                FROM orders o
                JOIN positions p ON o.position_id = p.id
                WHERE o.status = 'active'
            ''')
            rows = self.cursor.fetchall()
            
            orders = []
            for row in rows:
                order = {
                    'id': row[0],
                    'position_id': row[1],
                    'type': row[2],
                    'price': row[3],
                    'amount': row[4],
                    'status': row[5],
                    'created_at': row[6],
                    'executed_at': row[7],
                    'token_address': row[8],
                    'token_symbol': row[9]
                }
                orders.append(order)
                
            return orders
            
        except Exception as e:
            logger.error(f"Помилка отримання активних ордерів: {e}")
            return []
            
    def get_executed_orders(self, limit: int = 100) -> List[Dict]:
        """Отримання виконаних ордерів"""
        try:
            self._execute_with_retry('''
                SELECT o.*, p.token_address, p.token_symbol
                FROM orders o
                JOIN positions p ON o.position_id = p.id
                WHERE o.status = 'executed'
                ORDER BY o.executed_at DESC
                LIMIT ?
            ''', (limit,))
            
            columns = [description[0] for description in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"Помилка отримання виконаних ордерів: {e}")
            return []
            
    def delete_order(self, order_id: int) -> bool:
        """Видалення ордера"""
        try:
            self._execute_with_retry('''
                DELETE FROM orders
                WHERE id = ?
            ''', (order_id,))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Помилка видалення ордера: {e}")
            return False
            
    def add_trade_stats(self, stats: Dict) -> bool:
        """Додавання торгової статистики"""
        try:
            self._execute_with_retry('''
                INSERT INTO trade_stats (
                    session_id, period, start_time,
                    end_time, total_trades, win_rate,
                    total_profit, largest_win, largest_loss,
                    average_trade_time
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                stats['session_id'],
                stats['period'],
                stats['start_time'],
                stats['end_time'],
                stats['total_trades'],
                stats['win_rate'],
                stats['total_profit'],
                stats['largest_win'],
                stats['largest_loss'],
                stats['average_trade_time']
            ))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Помилка додавання торгової статистики: {e}")
            return False
            
    def get_trade_stats(self, session_id: str = None, period: str = None) -> List[Dict]:
        """Отримання торгової статистики"""
        try:
            if session_id and period:
                self._execute_with_retry('''
                    SELECT * FROM trade_stats
                    WHERE session_id = ? AND period = ?
                    ORDER BY start_time DESC
                ''', (session_id, period))
            elif session_id:
                self._execute_with_retry('''
                    SELECT * FROM trade_stats
                    WHERE session_id = ?
                    ORDER BY start_time DESC
                ''', (session_id,))
            elif period:
                self._execute_with_retry('''
                    SELECT * FROM trade_stats
                    WHERE period = ?
                    ORDER BY start_time DESC
                ''', (period,))
            else:
                self._execute_with_retry('''
                    SELECT * FROM trade_stats
                    ORDER BY start_time DESC
                ''')
            
            columns = [description[0] for description in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"Помилка отримання торгової статистики: {e}")
            return []
            
    def calculate_session_stats(self, session_id: str) -> Optional[Dict]:
        """Розрахунок статистики для сесії"""
        try:
            self._execute_with_retry('''
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                    SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
                    SUM(pnl) as total_profit,
                    MAX(pnl) as largest_win,
                    MIN(pnl) as largest_loss,
                    AVG(pnl) as average_profit,
                    COUNT(DISTINCT token_address) as unique_tokens,
                    SUM(amount) as total_volume
                FROM trades
                WHERE session_id = ?
                    AND status = 'closed'
            ''', (session_id,))
            
            result = self.cursor.fetchone()
            if result:
                columns = [description[0] for description in self.cursor.description]
                stats = dict(zip(columns, result))
                
                # Розрахунок додаткових метрик
                if stats['total_trades'] > 0:
                    stats['win_rate'] = (stats['winning_trades'] / stats['total_trades']) * 100
                    stats['average_trade_time'] = self._calculate_average_trade_time(session_id)
                else:
                    stats['win_rate'] = 0
                    stats['average_trade_time'] = 0
                    
                return stats
            return None
        except Exception as e:
            logger.error(f"Помилка розрахунку статистики сесії: {e}")
            return None
            
    def _calculate_average_trade_time(self, session_id: str) -> float:
        """Розрахунок середнього часу торгівлі"""
        try:
            self._execute_with_retry('''
                SELECT AVG(
                    CAST(
                        (JULIANDAY(updated_at) - JULIANDAY(created_at)) * 24 * 60 * 60
                        AS INTEGER
                    )
                ) as avg_time
                FROM trades
                WHERE session_id = ?
                    AND status = 'closed'
            ''', (session_id,))
            
            result = self.cursor.fetchone()
            return result[0] if result and result[0] is not None else 0
        except Exception as e:
            logger.error(f"Помилка розрахунку середнього часу торгівлі: {e}")
            return 0
            
    def get_token_performance(self, token_address: str) -> Optional[Dict]:
        """Отримання статистики продуктивності для токена"""
        try:
            self._execute_with_retry('''
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                    SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
                    SUM(pnl) as total_profit,
                    MAX(pnl) as largest_win,
                    MIN(pnl) as largest_loss,
                    AVG(pnl) as average_profit,
                    SUM(amount) as total_volume,
                    MIN(entry_price) as min_price,
                    MAX(entry_price) as max_price,
                    AVG(entry_price) as average_price
                FROM trades
                WHERE token_address = ?
                    AND status = 'closed'
            ''', (token_address,))
            
            result = self.cursor.fetchone()
            if result:
                columns = [description[0] for description in self.cursor.description]
                stats = dict(zip(columns, result))
                
                if stats['total_trades'] > 0:
                    stats['win_rate'] = (stats['winning_trades'] / stats['total_trades']) * 100
                else:
                    stats['win_rate'] = 0
                    
                return stats
            return None
        except Exception as e:
            logger.error(f"Помилка отримання статистики токена: {e}")
            return None
            
    def get_daily_performance(self, days: int = 30) -> List[Dict]:
        """Отримання щоденної статистики продуктивності"""
        try:
            self._execute_with_retry('''
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                    SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
                    SUM(pnl) as total_profit,
                    MAX(pnl) as largest_win,
                    MIN(pnl) as largest_loss,
                    AVG(pnl) as average_profit,
                    SUM(amount) as total_volume
                FROM trades
                WHERE created_at >= DATE('now', ?)
                    AND status = 'closed'
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            ''', (f'-{days} days',))
            
            columns = [description[0] for description in self.cursor.description]
            stats = []
            for row in self.cursor.fetchall():
                day_stats = dict(zip(columns, row))
                if day_stats['total_trades'] > 0:
                    day_stats['win_rate'] = (day_stats['winning_trades'] / day_stats['total_trades']) * 100
                else:
                    day_stats['win_rate'] = 0
                stats.append(day_stats)
            return stats
        except Exception as e:
            logger.error(f"Помилка отримання щоденної статистики: {e}")
            return []
            
    def close(self):
        """Закриття з'єднання з базою даних"""
        if self.conn:
            self.conn.close()

    def get_channels(self) -> List[Dict]:
        """Отримання списку всіх каналів"""
        try:
            self.cursor.execute('''
                SELECT id, name, type, status, settings, created_at, updated_at
                FROM channels
            ''')
            rows = self.cursor.fetchall()
            
            channels = []
            for row in rows:
                channel = {
                    'id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'status': row[3],
                    'settings': json.loads(row[4]) if row[4] else {},
                    'created_at': row[5],
                    'updated_at': row[6]
                }
                channels.append(channel)
                
            return channels
            
        except Exception as e:
            logger.error(f"Помилка отримання каналів: {e}")
            return []
            
    def get_active_channels(self) -> List[Dict]:
        """Отримання списку активних каналів"""
        try:
            self.cursor.execute('''
                SELECT id, name, type, status, settings, created_at, updated_at
                FROM channels
                WHERE status = 'active'
            ''')
            rows = self.cursor.fetchall()
            
            channels = []
            for row in rows:
                channel = {
                    'id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'status': row[3],
                    'settings': json.loads(row[4]) if row[4] else {},
                    'created_at': row[5],
                    'updated_at': row[6]
                }
                channels.append(channel)
                
            return channels
            
        except Exception as e:
            logger.error(f"Помилка отримання активних каналів: {e}")
            return []
            
    def get_channel_by_name(self, channel_name: str) -> Optional[Dict]:
        """Отримання каналу за назвою"""
        try:
            self._execute_with_retry('''
                SELECT id, name, type, status, settings
                FROM channels
                WHERE name = ?
            ''', (channel_name,))
            
            result = self.cursor.fetchone()
            if result:
                return {
                    'id': result[0],
                    'name': result[1],
                    'type': result[2],
                    'status': result[3],
                    'settings': json.loads(result[4]) if result[4] else {}
                }
            return None
            
        except Exception as e:
            logger.error(f"Помилка отримання каналу за назвою: {e}")
            return None
            
    def add_channel(self, channel: Dict) -> bool:
        """Додавання нового каналу"""
        try:
            # Спочатку перевіряємо чи канал вже існує
            self._execute_with_retry(
                "SELECT name FROM channels WHERE name = ?",
                (channel['name'],)
            )
            existing = self.cursor.fetchone()
            
            if existing:
                # Оновлюємо існуючий канал
                self._execute_with_retry('''
                    UPDATE channels 
                    SET type = ?, status = ?, settings = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE name = ?
                ''', (
                    channel.get('type', 'trading'),
                    channel.get('status', 'active'),
                    json.dumps(channel.get('settings', {})),
                    channel['name']
                ))
            else:
                # Додаємо новий канал
                self._execute_with_retry('''
                    INSERT INTO channels (
                        name, type, status, settings
                    )
                    VALUES (?, ?, ?, ?)
                ''', (
                    channel['name'],
                    channel.get('type', 'trading'),
                    channel.get('status', 'active'),
                    json.dumps(channel.get('settings', {}))
                ))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Помилка додавання каналу: {e}")
            return False
            
    def update_channel(self, name: str, updates: Dict) -> bool:
        """Оновлення каналу"""
        try:
            update_fields = []
            values = []
            for key, value in updates.items():
                if key == 'settings':
                    value = json.dumps(value)
                update_fields.append(f"{key} = ?")
                values.append(value)
            values.append(name)
            
            query = f'''
                UPDATE channels
                SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                WHERE name = ?
            '''
            
            self._execute_with_retry(query, tuple(values))
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Помилка оновлення каналу: {e}")
            return False
            
    def delete_channel(self, name: str) -> bool:
        """Видалення каналу"""
        try:
            self._execute_with_retry('''
                DELETE FROM channels
                WHERE name = ?
            ''', (name,))
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Помилка видалення каналу: {e}")
            return False
            
    def get_settings(self):
        """Отримати всі налаштування"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT key, value FROM settings")
            settings = {row[0]: row[1] for row in cursor.fetchall()}
            return settings
        except Exception as e:
            logger.error(f"Помилка при отриманні налаштувань: {e}")
            return {}
            
    def update_setting(self, key, value):
        """Оновити значення налаштування"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = ?",
                (key, value, value)
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Помилка при оновленні налаштування {key}: {e}")
            return False
            
    def update_channel_status(self, channel_name, status):
        """Оновлення статусу каналу"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE channels SET status = ? WHERE name = ?",
                (status, channel_name)
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Помилка при оновленні статусу каналу {channel_name}: {e}")
            return False
            
    def get_channel(self, channel_name):
        """Отримати інформацію про канал"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT name, type, status, settings FROM channels WHERE name = ?",
                (channel_name,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "name": row[0],
                    "type": row[1],
                    "status": row[2],
                    "settings": json.loads(row[3]) if row[3] else {}
                }
            return None
        except Exception as e:
            logger.error(f"Помилка при отриманні каналу {channel_name}: {e}")
            return None

    def get_token_info(self, token_address: str) -> Optional[Dict]:
        """Отримання інформації про токен"""
        try:
            self._execute_with_retry('''
                SELECT name, symbol, decimals
                FROM token_info
                WHERE address = ?
            ''', (token_address,))
            
            result = self.cursor.fetchone()
            if result:
                return {
                    "name": result[0],
                    "symbol": result[1],
                    "decimals": result[2]
                }
            return None
        except Exception as e:
            logger.error(f"Помилка отримання інформації про токен: {e}")
            return None

    def save_token_info(self, token_address: str, info: Dict) -> bool:
        """Збереження інформації про токен"""
        try:
            self._execute_with_retry('''
                INSERT OR REPLACE INTO token_info (
                    address, name, symbol, decimals
                )
                VALUES (?, ?, ?, ?)
            ''', (
                token_address,
                info['name'],
                info['symbol'],
                info['decimals']
            ))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Помилка збереження інформації про токен: {e}")
            return False 

    def _row_to_dict(self, row: tuple) -> dict:
        """Конвертація рядка в словник"""
        if not row:
            return {}
        columns = [description[0] for description in self.cursor.description]
        return dict(zip(columns, row))

    def _rows_to_list(self, rows: List[tuple]) -> List[dict]:
        """Конвертація списку рядків в список словників"""
        return [self._row_to_dict(row) for row in rows] 