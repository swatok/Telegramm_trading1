from typing import Dict, Any, List, Optional
import asyncpg
from datetime import datetime
from interfaces.database_interface import DatabaseInterface

class DatabaseImplementation(DatabaseInterface):
    """Імплементація для роботи з базою даних PostgreSQL"""
    
    def __init__(self):
        """Ініціалізація підключення до бази даних"""
        self.pool = None
        self.config = {}
        
    async def connect(self, config: Dict[str, Any]) -> bool:
        """Підключення до бази даних"""
        try:
            self.config = config
            
            # Створюємо пул підключень
            self.pool = await asyncpg.create_pool(
                host=config['db_host'],
                port=config['db_port'],
                database=config['db_name'],
                user=config['db_user'],
                password=config['db_password'],
                min_size=5,
                max_size=20
            )
            
            # Ініціалізуємо таблиці
            await self._initialize_tables()
            
            return True
            
        except Exception as e:
            print(f"Error connecting to database: {e}")
            return False
            
    async def disconnect(self) -> bool:
        """Відключення від бази даних"""
        try:
            if self.pool:
                await self.pool.close()
            return True
        except Exception as e:
            print(f"Error disconnecting from database: {e}")
            return False
            
    async def execute_query(self, query: str, params: Optional[List[Any]] = None) -> Optional[List[Dict[str, Any]]]:
        """Виконання SQL запиту"""
        try:
            async with self.pool.acquire() as connection:
                if query.lower().startswith('select'):
                    # Для SELECT запитів повертаємо результат
                    rows = await connection.fetch(query, *(params or []))
                    return [dict(row) for row in rows]
                else:
                    # Для інших запитів виконуємо і повертаємо статус
                    await connection.execute(query, *(params or []))
                    return []
                    
        except Exception as e:
            print(f"Error executing query: {e}")
            return None
            
    async def _initialize_tables(self) -> None:
        """Ініціалізація таблиць в базі даних"""
        try:
            async with self.pool.acquire() as connection:
                # Таблиця для торгових операцій
                await connection.execute('''
                    CREATE TABLE IF NOT EXISTS trades (
                        id SERIAL PRIMARY KEY,
                        token_address VARCHAR(44) NOT NULL,
                        operation_type VARCHAR(10) NOT NULL,
                        amount DECIMAL NOT NULL,
                        price DECIMAL NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        status VARCHAR(20) NOT NULL,
                        transaction_id VARCHAR(88),
                        error_message TEXT
                    )
                ''')
                
                # Таблиця для балансів гаманця
                await connection.execute('''
                    CREATE TABLE IF NOT EXISTS wallet_balances (
                        id SERIAL PRIMARY KEY,
                        token_address VARCHAR(44) NOT NULL,
                        balance DECIMAL NOT NULL,
                        timestamp TIMESTAMP NOT NULL
                    )
                ''')
                
                # Таблиця для ринкових даних
                await connection.execute('''
                    CREATE TABLE IF NOT EXISTS market_data (
                        id SERIAL PRIMARY KEY,
                        token_address VARCHAR(44) NOT NULL,
                        price DECIMAL NOT NULL,
                        volume DECIMAL NOT NULL,
                        timestamp TIMESTAMP NOT NULL
                    )
                ''')
                
                # Таблиця для логів
                await connection.execute('''
                    CREATE TABLE IF NOT EXISTS logs (
                        id SERIAL PRIMARY KEY,
                        level VARCHAR(10) NOT NULL,
                        message TEXT NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        metadata JSONB
                    )
                ''')
                
        except Exception as e:
            print(f"Error initializing tables: {e}")
            
    async def save_trade(self, trade_data: Dict[str, Any]) -> bool:
        """Збереження торгової операції"""
        try:
            query = '''
                INSERT INTO trades (
                    token_address, operation_type, amount, price, 
                    timestamp, status, transaction_id, error_message
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            '''
            
            params = [
                trade_data['token_address'],
                trade_data['operation_type'],
                trade_data['amount'],
                trade_data['price'],
                trade_data.get('timestamp', datetime.now()),
                trade_data['status'],
                trade_data.get('transaction_id'),
                trade_data.get('error_message')
            ]
            
            await self.execute_query(query, params)
            return True
            
        except Exception as e:
            print(f"Error saving trade: {e}")
            return False
            
    async def update_balance(self, balance_data: Dict[str, Any]) -> bool:
        """Оновлення балансу гаманця"""
        try:
            query = '''
                INSERT INTO wallet_balances (token_address, balance, timestamp)
                VALUES ($1, $2, $3)
            '''
            
            params = [
                balance_data['token_address'],
                balance_data['balance'],
                balance_data.get('timestamp', datetime.now())
            ]
            
            await self.execute_query(query, params)
            return True
            
        except Exception as e:
            print(f"Error updating balance: {e}")
            return False
            
    async def save_market_data(self, market_data: Dict[str, Any]) -> bool:
        """Збереження ринкових даних"""
        try:
            query = '''
                INSERT INTO market_data (token_address, price, volume, timestamp)
                VALUES ($1, $2, $3, $4)
            '''
            
            params = [
                market_data['token_address'],
                market_data['price'],
                market_data['volume'],
                market_data.get('timestamp', datetime.now())
            ]
            
            await self.execute_query(query, params)
            return True
            
        except Exception as e:
            print(f"Error saving market data: {e}")
            return False
            
    async def save_log(self, log_data: Dict[str, Any]) -> bool:
        """Збереження логу"""
        try:
            query = '''
                INSERT INTO logs (level, message, timestamp, metadata)
                VALUES ($1, $2, $3, $4)
            '''
            
            params = [
                log_data['level'],
                log_data['message'],
                log_data.get('timestamp', datetime.now()),
                log_data.get('metadata', {})
            ]
            
            await self.execute_query(query, params)
            return True
            
        except Exception as e:
            print(f"Error saving log: {e}")
            return False 