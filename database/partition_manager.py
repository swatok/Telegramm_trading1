"""Модуль для керування партиціями"""

from typing import Dict, List, Optional
from datetime import date, datetime, timedelta
from loguru import logger
from .postgres_connection import PostgresConnection

class PartitionManager:
    """Клас для керування партиціями в PostgreSQL"""
    
    def __init__(self, postgres_connection: PostgresConnection):
        """
        Ініціалізація менеджера партицій
        
        Args:
            postgres_connection: Об'єкт підключення до PostgreSQL
        """
        self.postgres = postgres_connection
        
    def setup_partitions(self) -> None:
        """Налаштування партиціонування таблиць"""
        try:
            # Створюємо партиційовані таблиці
            self.postgres.execute_query("""
                -- Партиціонована таблиця для сигналів
                CREATE TABLE IF NOT EXISTS signals_partitioned (
                    id SERIAL,
                    channel_id INTEGER REFERENCES channels(id),
                    message_id BIGINT NOT NULL,
                    pair VARCHAR(50) NOT NULL,
                    direction VARCHAR(10) NOT NULL,
                    entry_price DECIMAL(20, 8) NOT NULL,
                    take_profit DECIMAL(20, 8),
                    stop_loss DECIMAL(20, 8),
                    status VARCHAR(20) DEFAULT 'new',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP WITH TIME ZONE,
                    metadata JSONB DEFAULT '{}'::jsonb,
                    UNIQUE(channel_id, message_id)
                ) PARTITION BY RANGE (created_at);
                
                -- Партиціонована таблиця для позицій
                CREATE TABLE IF NOT EXISTS positions_partitioned (
                    id SERIAL,
                    channel_id INTEGER REFERENCES channels(id),
                    pair VARCHAR(50) NOT NULL,
                    entry_price DECIMAL(20, 8) NOT NULL,
                    take_profit DECIMAL(20, 8),
                    stop_loss DECIMAL(20, 8),
                    direction VARCHAR(10) NOT NULL,
                    status VARCHAR(20) DEFAULT 'open',
                    opened_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP WITH TIME ZONE,
                    close_price DECIMAL(20, 8),
                    profit_loss DECIMAL(20, 8),
                    signal_message_id BIGINT,
                    close_message_id BIGINT,
                    metadata JSONB DEFAULT '{}'::jsonb
                ) PARTITION BY RANGE (opened_at);
                
                -- Партиціонована таблиця для щоденної статистики
                CREATE TABLE IF NOT EXISTS daily_stats_partitioned (
                    id SERIAL,
                    date DATE NOT NULL,
                    total_signals INTEGER DEFAULT 0,
                    processed_signals INTEGER DEFAULT 0,
                    failed_signals INTEGER DEFAULT 0,
                    total_positions INTEGER DEFAULT 0,
                    closed_positions INTEGER DEFAULT 0,
                    total_profit DECIMAL(20, 8) DEFAULT 0,
                    avg_profit DECIMAL(20, 8) DEFAULT 0,
                    win_rate DECIMAL(5, 2) DEFAULT 0,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date)
                ) PARTITION BY RANGE (date);
                
                -- Партиціонована таблиця для статистики каналів
                CREATE TABLE IF NOT EXISTS channel_stats_partitioned (
                    id SERIAL,
                    channel_id INTEGER REFERENCES channels(id),
                    date DATE NOT NULL,
                    total_signals INTEGER DEFAULT 0,
                    processed_signals INTEGER DEFAULT 0,
                    failed_signals INTEGER DEFAULT 0,
                    total_positions INTEGER DEFAULT 0,
                    closed_positions INTEGER DEFAULT 0,
                    total_profit DECIMAL(20, 8) DEFAULT 0,
                    avg_profit DECIMAL(20, 8) DEFAULT 0,
                    win_rate DECIMAL(5, 2) DEFAULT 0,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(channel_id, date)
                ) PARTITION BY RANGE (date);
                
                -- Партиціонована таблиця для статистики пар
                CREATE TABLE IF NOT EXISTS pair_stats_partitioned (
                    id SERIAL,
                    pair VARCHAR(50) NOT NULL,
                    date DATE NOT NULL,
                    total_signals INTEGER DEFAULT 0,
                    processed_signals INTEGER DEFAULT 0,
                    failed_signals INTEGER DEFAULT 0,
                    total_positions INTEGER DEFAULT 0,
                    closed_positions INTEGER DEFAULT 0,
                    total_profit DECIMAL(20, 8) DEFAULT 0,
                    avg_profit DECIMAL(20, 8) DEFAULT 0,
                    win_rate DECIMAL(5, 2) DEFAULT 0,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(pair, date)
                ) PARTITION BY RANGE (date);
            """)
            
            logger.info("Створено партиційовані таблиці")
            
        except Exception as e:
            logger.error(f"Помилка створення партиційованих таблиць: {e}")
            raise
            
    def create_partition(
        self,
        table_name: str,
        start_date: date,
        end_date: date
    ) -> None:
        """
        Створення партиції для таблиці
        
        Args:
            table_name: Назва таблиці
            start_date: Початкова дата
            end_date: Кінцева дата
        """
        try:
            partition_name = f"{table_name}_{start_date.strftime('%Y_%m')}"
            
            self.postgres.execute_query(f"""
                CREATE TABLE IF NOT EXISTS {partition_name}
                PARTITION OF {table_name}_partitioned
                FOR VALUES FROM ('{start_date}') TO ('{end_date}')
            """)
            
            logger.info(f"Створено партицію {partition_name}")
            
        except Exception as e:
            logger.error(f"Помилка створення партиції: {e}")
            raise
            
    def create_future_partitions(
        self,
        table_name: str,
        months_ahead: int = 3
    ) -> None:
        """
        Створення майбутніх партицій
        
        Args:
            table_name: Назва таблиці
            months_ahead: Кількість місяців вперед
        """
        try:
            current_date = date.today().replace(day=1)
            
            for _ in range(months_ahead):
                next_month = current_date.replace(
                    day=28
                ) + timedelta(days=4)
                next_month = next_month.replace(day=1)
                
                self.create_partition(
                    table_name,
                    current_date,
                    next_month
                )
                
                current_date = next_month
                
            logger.info(
                f"Створено {months_ahead} майбутніх партицій "
                f"для таблиці {table_name}"
            )
            
        except Exception as e:
            logger.error(f"Помилка створення майбутніх партицій: {e}")
            raise
            
    def migrate_to_partitions(
        self,
        table_name: str,
        batch_size: int = 1000
    ) -> None:
        """
        Міграція даних в партиційовану таблицю
        
        Args:
            table_name: Назва таблиці
            batch_size: Розмір пакету для міграції
        """
        try:
            # Отримуємо загальну кількість записів
            result = self.postgres.execute_query(
                f"SELECT COUNT(*) FROM {table_name}",
                fetch=True
            )
            total_records = result[0]['count']
            
            if total_records == 0:
                logger.info(f"Немає даних для міграції в таблиці {table_name}")
                return
                
            # Мігруємо дані пакетами
            offset = 0
            while offset < total_records:
                self.postgres.execute_query(f"""
                    INSERT INTO {table_name}_partitioned
                    SELECT *
                    FROM {table_name}
                    ORDER BY id
                    LIMIT {batch_size}
                    OFFSET {offset}
                """)
                
                offset += batch_size
                logger.info(
                    f"Мігровано {min(offset, total_records)} з {total_records} "
                    f"записів таблиці {table_name}"
                )
                
            logger.info(f"Завершено міграцію даних таблиці {table_name}")
            
        except Exception as e:
            logger.error(f"Помилка міграції даних: {e}")
            raise
            
    def cleanup_old_partitions(
        self,
        table_name: str,
        months_to_keep: int = 12
    ) -> None:
        """
        Очищення старих партицій
        
        Args:
            table_name: Назва таблиці
            months_to_keep: Кількість місяців для зберігання
        """
        try:
            # Отримуємо список партицій
            partitions = self.postgres.execute_query(
                f"""
                SELECT child.relname as partition_name,
                       pg_get_expr(child.relpartbound, child.oid) as partition_range
                FROM pg_inherits
                JOIN pg_class parent ON pg_inherits.inhparent = parent.oid
                JOIN pg_class child ON pg_inherits.inhrelid = child.oid
                WHERE parent.relname = '{table_name}_partitioned'
                ORDER BY child.relname
                """,
                fetch=True
            )
            
            if not partitions:
                logger.info(f"Немає партицій для очищення в таблиці {table_name}")
                return
                
            # Визначаємо дату, старіше якої партиції будуть видалені
            cutoff_date = date.today().replace(
                day=1
            ) - timedelta(days=months_to_keep * 30)
            
            # Видаляємо старі партиції
            for partition in partitions:
                # Отримуємо дату з діапазону партиції
                partition_range = partition['partition_range']
                start_date_str = partition_range.split("'")[1]
                start_date = datetime.strptime(
                    start_date_str,
                    '%Y-%m-%d'
                ).date()
                
                if start_date < cutoff_date:
                    self.postgres.execute_query(
                        f"DROP TABLE {partition['partition_name']}"
                    )
                    logger.info(f"Видалено партицію {partition['partition_name']}")
                    
            logger.info(
                f"Завершено очищення старих партицій таблиці {table_name}"
            )
            
        except Exception as e:
            logger.error(f"Помилка очищення старих партицій: {e}")
            raise
            
    def get_partition_info(self, table_name: str) -> List[Dict]:
        """
        Отримання інформації про партиції
        
        Args:
            table_name: Назва таблиці
            
        Returns:
            Список словників з інформацією про партиції
        """
        try:
            return self.postgres.execute_query(
                f"""
                SELECT child.relname as partition_name,
                       pg_get_expr(child.relpartbound, child.oid) as partition_range,
                       pg_size_pretty(pg_relation_size(child.oid)) as size,
                       pg_stat_get_live_tuples(child.oid) as live_tuples,
                       pg_stat_get_dead_tuples(child.oid) as dead_tuples
                FROM pg_inherits
                JOIN pg_class parent ON pg_inherits.inhparent = parent.oid
                JOIN pg_class child ON pg_inherits.inhrelid = child.oid
                WHERE parent.relname = '{table_name}_partitioned'
                ORDER BY child.relname
                """,
                fetch=True
            ) or []
            
        except Exception as e:
            logger.error(f"Помилка отримання інформації про партиції: {e}")
            raise 