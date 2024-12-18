import sqlite3
import logging
from datetime import datetime
import time
from typing import List, Dict

# Налаштування логування
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.db_file = 'trading_bot.db'
        self.conn = None
        self.cursor = None
        self._create_tables()
        
    def _create_tables(self):
        """Створення таблиць в базі даних"""
        try:
            self.conn = sqlite3.connect(self.db_file)
            self.cursor = self.conn.cursor()
            
            # Таблиця для сесій бота
            self._execute_with_retry('''
                CREATE TABLE IF NOT EXISTS bot_sessions (
                    id TEXT PRIMARY KEY,
                    start_time TIMESTAMP,
                    last_update TIMESTAMP,
                    status TEXT DEFAULT 'active'
                )
            ''')
            
            # Таблиця для транзакцій
            self._execute_with_retry('''
                CREATE TABLE IF NOT EXISTS transactions (
                    signature TEXT PRIMARY KEY,
                    token_address TEXT,
                    amount REAL,
                    type TEXT,
                    status TEXT,
                    confirmations INTEGER DEFAULT 0,
                    balance_change REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблиця для сигналів
            self._execute_with_retry('''
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id INTEGER,
                    channel_id INTEGER,
                    token_address TEXT,
                    token_name TEXT,
                    signal_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблиця для трейдів
            self._execute_with_retry('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token_address TEXT,
                    token_name TEXT,
                    entry_price REAL,
                    amount REAL,
                    status TEXT DEFAULT 'ACTIVE',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_tx TEXT
                )
            ''')
            
            # Таблиця для цін
            self._execute_with_retry('''
                CREATE TABLE IF NOT EXISTS prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token_address TEXT,
                    price REAL,
                    volume_24h REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            self.conn.commit()
            logger.info("Таблиці успішно створені")
            
        except Exception as e:
            logger.error(f"Помилка створення таблиць: {e}")
            if self.conn:
                self.conn.close()
            raise
            
    def _execute_with_retry(self, sql, params=None, max_retries=3, retry_delay=1):
        """Виконання SQL запиту з повторними спробами"""
        for attempt in range(max_retries):
            try:
                if params:
                    result = self.cursor.execute(sql, params)
                else:
                    result = self.cursor.execute(sql)
                return result
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    logger.warning(f"База даних заблокована, спроба {attempt + 1}/{max_retries}")
                    time.sleep(retry_delay)
                else:
                    raise
                    
    def add_signal(self, message_id: int, channel_id: int, token_address: str, token_name: str, signal_type: str):
        """Додавання нового сигналу"""
        try:
            logger.debug(f"Додавання нового сигналу: {token_address} {signal_type}")
            self._execute_with_retry('''
                INSERT INTO signals (message_id, channel_id, token_address, token_name, signal_type)
                VALUES (?, ?, ?, ?, ?)
            ''', (message_id, channel_id, token_address, token_name, signal_type))
            signal_id = self.cursor.lastrowid
            logger.info(f"Сигнал успішно додано: {token_address} (ID: {signal_id})")
            return signal_id
        except Exception as e:
            logger.error(f"Помилка додавання сигналу: {e}", exc_info=True)
            return None
            
    def add_trade(self, token_address: str, token_name: str, entry_price: float, amount: float):
        """Додавання нової торгової операції"""
        try:
            logger.debug(f"Додавання нової торгової операції: {token_address}")
            self._execute_with_retry('''
                INSERT INTO trades (token_address, token_name, entry_price, amount)
                VALUES (?, ?, ?, ?)
            ''', (token_address, token_name, entry_price, amount))
            trade_id = self.cursor.lastrowid
            logger.info(f"Торгова операція успішно додана: {token_address} (ID: {trade_id})")
            return trade_id
        except Exception as e:
            logger.error(f"Помилка додавання торгової операції: {e}", exc_info=True)
            return None
            
    def add_trade_exit(self, trade_id: int, exit_price: float, amount: float, profit_percentage: float):
        """Додавання виходу з торгової операції"""
        try:
            logger.debug(f"Додавання виходу з торгової операції: {trade_id}")
            self._execute_with_retry('''
                INSERT INTO trade_exits (trade_id, exit_price, amount, profit_percentage)
                VALUES (?, ?, ?, ?)
            ''', (trade_id, exit_price, amount, profit_percentage))
            exit_id = self.cursor.lastrowid
            logger.info(f"Вихід з торгової операції успішно додано: {trade_id} (ID: {exit_id})")
            return exit_id
        except Exception as e:
            logger.error(f"Помилка додавання виходу з торгової операції: {e}", exc_info=True)
            return None
            
    def add_price(self, token_address: str, price: float, volume_24h: float = None):
        """Додавання нової ціни токена"""
        try:
            logger.debug(f"Додавання нової ціни для токена {token_address}: {price}")
            self._execute_with_retry('''
                INSERT INTO prices (token_address, price, volume_24h)
                VALUES (?, ?, ?)
            ''', (token_address, price, volume_24h))
            price_id = self.cursor.lastrowid
            logger.info(f"Ціна успішно додана: {token_address} (ID: {price_id})")
            return price_id
        except Exception as e:
            logger.error(f"Помилка додавання ціни: {e}", exc_info=True)
            return None
            
    def update_trade_status(self, trade_id: int, status: str):
        """Оновлення статусу торгової операції"""
        try:
            logger.debug(f"Оновлення статусу торгової операції {trade_id} на {status}")
            self._execute_with_retry('''
                UPDATE trades
                SET status = ?
                WHERE id = ?
            ''', (status, trade_id))
            logger.info(f"Статус торгової операції {trade_id} оновлено на {status}")
        except Exception as e:
            logger.error(f"Помилка оновлення статусу торгової операції: {e}", exc_info=True)
            
    def get_active_trades(self):
        """Отримання активних торгових операцій"""
        try:
            logger.debug("Отримання списку активних торгових операцій")
            self._execute_with_retry('''
                SELECT * FROM trades
                WHERE status = 'ACTIVE'
                ORDER BY created_at DESC
            ''')
            trades = self.cursor.fetchall()
            logger.info(f"Знайдено {len(trades)} активних торгових операцій")
            return trades
        except Exception as e:
            logger.error(f"Помилка отримання активних торгових операцій: {e}", exc_info=True)
            return []
            
    def update_balance(self, token_address: str, amount: float):
        """Оновлення балансу токена"""
        try:
            logger.debug(f"Оновлення балансу для токена {token_address}: {amount}")
            self._execute_with_retry('''
                INSERT OR REPLACE INTO balances (token_address, amount, last_updated)
                VALUES (?, ?, ?)
            ''', (token_address, amount, datetime.now()))
            logger.info(f"Баланс токена {token_address} оновлено")
        except Exception as e:
            logger.error(f"Помилка оновлення балансу: {e}", exc_info=True)
            
    def get_balance(self, token_address: str) -> float:
        """Отримання балансу токена"""
        try:
            logger.debug(f"Отримання балансу для токена {token_address}")
            self._execute_with_retry('''
                SELECT amount FROM balances
                WHERE token_address = ?
            ''', (token_address,))
            result = self.cursor.fetchone()
            balance = result[0] if result else 0.0
            logger.info(f"Отримано баланс для токена {token_address}: {balance}")
            return balance
        except Exception as e:
            logger.error(f"Помилка отримання балансу: {e}", exc_info=True)
            return 0.0
            
    def get_signal_by_message(self, message_id: int, channel_id: int) -> dict:
        """Отримання сигналу за ID повідомлення та каналу"""
        try:
            logger.debug(f"Отримання сигналу для message_id={message_id}, channel_id={channel_id}")
            self._execute_with_retry("""
                SELECT * FROM signals 
                WHERE message_id = ? AND channel_id = ?
            """, (message_id, channel_id))
            row = self.cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'message_id': row[1],
                    'channel_id': row[2],
                    'token_address': row[3],
                    'token_name': row[4],
                    'signal_type': row[5],
                    'timestamp': row[6]
                }
            logger.debug("Сигнал не знайдено")
            return None
        except Exception as e:
            logger.error(f"Помилка отримання сигналу: {e}", exc_info=True)
            return None
            
    def add_bot_session(self, session_id: str, start_time: datetime):
        """Додавання нової сесії бота"""
        try:
            self.cursor.execute(
                'INSERT INTO bot_sessions (id, start_time, last_update) VALUES (?, ?, ?)',
                (session_id, start_time, start_time)
            )
            self.conn.commit()
        except Exception as e:
            logger.error(f"Помилка додавання сесії бота: {e}")
            raise
            
    def update_bot_session_status(self, session_id: str, status: str):
        """Оновлення статусу сесії бота"""
        try:
            self.cursor.execute(
                'UPDATE bot_sessions SET status = ?, last_update = ? WHERE id = ?',
                (status, datetime.now(), session_id)
            )
            self.conn.commit()
        except Exception as e:
            logger.error(f"Помилка оновлення статусу сесії: {e}")
            raise
            
    def get_active_bot_sessions(self) -> List[Dict]:
        """Отримання активних сесій бота"""
        try:
            self.cursor.execute(
                'SELECT * FROM bot_sessions WHERE status = "active" ORDER BY start_time DESC'
            )
            columns = [description[0] for description in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"Помилка отримання активних сесій: {e}")
            return []
            
    def add_transaction(self, signature: str, token_address: str, amount: float, type: str, status: str):
        """Додавання нової транзакції"""
        try:
            logger.debug(f"Додавання нової транзакції: {signature}")
            self._execute_with_retry('''
                INSERT INTO transactions (signature, token_address, amount, type, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (signature, token_address, amount, type, status))
            self.conn.commit()
            logger.info(f"Транзакцію успішно додано: {signature}")
            return True
        except Exception as e:
            logger.error(f"Помилка додавання транзакції: {e}", exc_info=True)
            return False
            
    def update_transaction_status(self, signature: str, status: str, confirmations: int = None, balance_change: float = None):
        """Оновлення статусу транзакції"""
        try:
            logger.debug(f"Оновлення статусу транзакції {signature} на {status}")
            update_fields = ['status']
            update_values = [status]
            
            if confirmations is not None:
                update_fields.append('confirmations')
                update_values.append(confirmations)
                
            if balance_change is not None:
                update_fields.append('balance_change')
                update_values.append(balance_change)
                
            update_fields.append('updated_at')
            update_values.append(datetime.now())
            
            # Формуємо SQL запит
            sql = f'''
                UPDATE transactions
                SET {', '.join(f'{field} = ?' for field in update_fields)}
                WHERE signature = ?
            '''
            update_values.append(signature)
            
            self._execute_with_retry(sql, tuple(update_values))
            self.conn.commit()
            logger.info(f"Статус транзакції {signature} оновлено на {status}")
            return True
        except Exception as e:
            logger.error(f"Помилка оновлення статусу транзакції: {e}", exc_info=True)
            return False
            
    def get_transaction(self, signature: str) -> dict:
        """Отримання інформації про транзакцію"""
        try:
            logger.debug(f"Отримання інформації про транзакцію: {signature}")
            self._execute_with_retry('''
                SELECT * FROM transactions
                WHERE signature = ?
            ''', (signature,))
            row = self.cursor.fetchone()
            if row:
                columns = [description[0] for description in self.cursor.description]
                return dict(zip(columns, row))
            return None
        except Exception as e:
            logger.error(f"Помилка отримання інформації про транзакцію: {e}", exc_info=True)
            return None
            
    def get_recent_transactions(self, limit: int = 10) -> List[Dict]:
        """Отримання останніх транзакцій"""
        try:
            logger.debug(f"Отримання останніх {limit} транзакцій")
            self._execute_with_retry('''
                SELECT * FROM transactions
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
            rows = self.cursor.fetchall()
            if rows:
                columns = [description[0] for description in self.cursor.description]
                return [dict(zip(columns, row)) for row in rows]
            return []
        except Exception as e:
            logger.error(f"Помилка отримання останніх транзакцій: {e}", exc_info=True)
            return []
            
    def __del__(self):
        """Закриття з'єднання з базою даних"""
        try:
            if self.conn:
                self.conn.close()
                logger.info("З'єднання з базою даних закрито")
        except Exception as e:
            logger.error(f"Помилка закриття з'єднання з базою даних: {e}") 