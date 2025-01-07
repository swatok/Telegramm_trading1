"""Position repository"""

from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from .base_repository import BaseRepository
from models.position import Position

class PositionRepository(BaseRepository):
    """Репозиторій для роботи з позиціями"""
    
    async def create_tables(self) -> None:
        """Створення необхідних таблиць"""
        await self.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                id SERIAL PRIMARY KEY,
                token_address TEXT NOT NULL,
                amount DECIMAL NOT NULL,
                entry_price DECIMAL NOT NULL,
                current_price DECIMAL NOT NULL,
                take_profit_levels DECIMAL[] DEFAULT ARRAY[]::DECIMAL[],
                stop_loss_level DECIMAL,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW()
            );
            
            CREATE TABLE IF NOT EXISTS position_history (
                id SERIAL PRIMARY KEY,
                position_id INTEGER REFERENCES positions(id) ON DELETE CASCADE,
                price DECIMAL NOT NULL,
                timestamp TIMESTAMP NOT NULL DEFAULT NOW()
            );
        """)
    
    async def save_position(self, position: Position) -> bool:
        """Збереження позиції"""
        try:
            position_id = await self.fetchval("""
                INSERT INTO positions (
                    token_address, amount, entry_price, current_price,
                    take_profit_levels, stop_loss_level, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (token_address) 
                DO UPDATE SET 
                    amount = EXCLUDED.amount,
                    current_price = EXCLUDED.current_price,
                    take_profit_levels = EXCLUDED.take_profit_levels,
                    stop_loss_level = EXCLUDED.stop_loss_level,
                    updated_at = EXCLUDED.updated_at
                RETURNING id
            """,
            position.token_address,
            position.amount,
            position.entry_price,
            position.current_price,
            position.take_profit_levels,
            position.stop_loss_level,
            position.created_at,
            position.updated_at
            )
            
            # Зберігаємо історію цін
            await self.execute("""
                INSERT INTO position_history (position_id, price)
                VALUES ($1, $2)
            """, position_id, position.current_price)
            
            return True
            
        except Exception as e:
            print(f"Error saving position: {e}")
            return False
    
    async def get_position(self, token_address: str) -> Optional[Position]:
        """Отримання позиції за адресою токена"""
        position_data = await self.fetchrow("""
            SELECT * FROM positions WHERE token_address = $1
        """, token_address)
        
        if not position_data:
            return None
            
        return Position(
            token_address=position_data['token_address'],
            amount=position_data['amount'],
            entry_price=position_data['entry_price'],
            current_price=position_data['current_price'],
            take_profit_levels=position_data['take_profit_levels'],
            stop_loss_level=position_data['stop_loss_level'],
            created_at=position_data['created_at'],
            updated_at=position_data['updated_at']
        )
    
    async def get_position_history(
        self,
        token_address: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[tuple[datetime, Decimal]]:
        """Отримання історії цін позиції"""
        history_data = await self.fetch("""
            SELECT ph.timestamp, ph.price
            FROM position_history ph
            JOIN positions p ON p.id = ph.position_id
            WHERE p.token_address = $1
            AND ph.timestamp BETWEEN $2 AND $3
            ORDER BY ph.timestamp ASC
        """, token_address, start_date, end_date)
        
        return [(data['timestamp'], data['price']) for data in history_data]
    
    async def delete_position(self, token_address: str) -> bool:
        """Видалення позиції"""
        try:
            await self.execute("""
                DELETE FROM positions WHERE token_address = $1
            """, token_address)
            return True
        except Exception as e:
            print(f"Error deleting position: {e}")
            return False
    
    async def get_all_positions(self) -> List[Position]:
        """Отримання всіх позицій"""
        positions = []
        position_data = await self.fetch("SELECT * FROM positions")
        
        for data in position_data:
            position = Position(
                token_address=data['token_address'],
                amount=data['amount'],
                entry_price=data['entry_price'],
                current_price=data['current_price'],
                take_profit_levels=data['take_profit_levels'],
                stop_loss_level=data['stop_loss_level'],
                created_at=data['created_at'],
                updated_at=data['updated_at']
            )
            positions.append(position)
            
        return positions
    
    async def update_position_price(
        self,
        token_address: str,
        new_price: Decimal
    ) -> bool:
        """Оновлення ціни позиції"""
        try:
            position_id = await self.fetchval("""
                UPDATE positions 
                SET current_price = $1, updated_at = NOW()
                WHERE token_address = $2
                RETURNING id
            """, new_price, token_address)
            
            if position_id:
                await self.execute("""
                    INSERT INTO position_history (position_id, price)
                    VALUES ($1, $2)
                """, position_id, new_price)
                
            return bool(position_id)
            
        except Exception as e:
            print(f"Error updating position price: {e}")
            return False
