"""Portfolio repository"""

from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from .base_repository import BaseRepository
from models.portfolio import Portfolio
from models.position import Position

class PortfolioRepository(BaseRepository):
    """Репозиторій для роботи з портфелем"""
    
    async def create_tables(self) -> None:
        """Створення необхідних таблиць"""
        await self.execute("""
            CREATE TABLE IF NOT EXISTS portfolios (
                id SERIAL PRIMARY KEY,
                wallet_address TEXT NOT NULL UNIQUE,
                total_value DECIMAL NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW()
            );
            
            CREATE TABLE IF NOT EXISTS positions (
                id SERIAL PRIMARY KEY,
                portfolio_id INTEGER REFERENCES portfolios(id),
                token_address TEXT NOT NULL,
                amount DECIMAL NOT NULL,
                entry_price DECIMAL NOT NULL,
                current_price DECIMAL NOT NULL,
                take_profit_levels DECIMAL[] DEFAULT ARRAY[]::DECIMAL[],
                stop_loss_level DECIMAL,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                UNIQUE(portfolio_id, token_address)
            );
        """)
    
    async def get_portfolio(self, wallet_address: str) -> Optional[Portfolio]:
        """Отримання портфеля за адресою гаманця"""
        portfolio_data = await self.fetchrow("""
            SELECT * FROM portfolios WHERE wallet_address = $1
        """, wallet_address)
        
        if not portfolio_data:
            return None
            
        positions = await self.fetch("""
            SELECT * FROM positions 
            WHERE portfolio_id = $1
        """, portfolio_data['id'])
        
        portfolio = Portfolio(
            wallet_address=portfolio_data['wallet_address'],
            total_value=portfolio_data['total_value'],
            created_at=portfolio_data['created_at'],
            updated_at=portfolio_data['updated_at']
        )
        
        for pos in positions:
            position = Position(
                token_address=pos['token_address'],
                amount=pos['amount'],
                entry_price=pos['entry_price'],
                current_price=pos['current_price'],
                created_at=pos['created_at'],
                updated_at=pos['updated_at'],
                take_profit_levels=pos['take_profit_levels'],
                stop_loss_level=pos['stop_loss_level']
            )
            portfolio.add_position(position)
            
        return portfolio
    
    async def save_portfolio(self, portfolio: Portfolio) -> bool:
        """Збереження портфеля"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                try:
                    # Зберігаємо або оновлюємо портфель
                    portfolio_id = await conn.fetchval("""
                        INSERT INTO portfolios (
                            wallet_address, total_value, created_at, updated_at
                        ) VALUES ($1, $2, $3, $4)
                        ON CONFLICT (wallet_address) 
                        DO UPDATE SET 
                            total_value = EXCLUDED.total_value,
                            updated_at = EXCLUDED.updated_at
                        RETURNING id
                    """, 
                    portfolio.wallet_address,
                    portfolio.total_value,
                    portfolio.created_at,
                    portfolio.updated_at
                    )
                    
                    # Видаляємо старі позиції
                    await conn.execute("""
                        DELETE FROM positions WHERE portfolio_id = $1
                    """, portfolio_id)
                    
                    # Додаємо нові позиції
                    for position in portfolio.positions.values():
                        await conn.execute("""
                            INSERT INTO positions (
                                portfolio_id, token_address, amount,
                                entry_price, current_price, take_profit_levels,
                                stop_loss_level, created_at, updated_at
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        """,
                        portfolio_id,
                        position.token_address,
                        position.amount,
                        position.entry_price,
                        position.current_price,
                        position.take_profit_levels,
                        position.stop_loss_level,
                        position.created_at,
                        position.updated_at
                        )
                    
                    return True
                    
                except Exception as e:
                    print(f"Error saving portfolio: {e}")
                    return False
    
    async def delete_portfolio(self, wallet_address: str) -> bool:
        """Видалення портфеля"""
        try:
            await self.execute("""
                DELETE FROM portfolios WHERE wallet_address = $1
            """, wallet_address)
            return True
        except Exception as e:
            print(f"Error deleting portfolio: {e}")
            return False
    
    async def get_all_portfolios(self) -> List[Portfolio]:
        """Отримання всіх портфелів"""
        portfolios = []
        portfolio_data = await self.fetch("SELECT wallet_address FROM portfolios")
        
        for data in portfolio_data:
            portfolio = await self.get_portfolio(data['wallet_address'])
            if portfolio:
                portfolios.append(portfolio)
                
        return portfolios 