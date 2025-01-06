from typing import Optional
from aiogram import Bot, Dispatcher
from aiogram.types import Message

from interfaces.telegram_interfaces import BaseService
from trading.position_manager import PositionManager
from trading.trade_validator import TradeValidator
from trading.price_calculator import PriceCalculator
from solana import SolanaClient

class ManagementBot(BaseService):
    """Main management bot for trading operations"""
    
    def __init__(self, token: str, admin_ids: list[int], solana_endpoint: str):
        """Initialize bot with token and admin IDs"""
        self.bot = Bot(token=token)
        self.dp = Dispatcher(self.bot)
        self.admin_ids = admin_ids
        
        # Initialize trading components
        self.position_manager = PositionManager()
        self.trade_validator = TradeValidator()
        self.price_calculator = PriceCalculator()
        
        # Initialize Solana client
        self.solana = SolanaClient()
        self.solana_endpoint = solana_endpoint
        
        self._setup_handlers()
    
    def _setup_handlers(self) -> None:
        """Setup message handlers"""
        # Admin commands
        self.dp.register_message_handler(
            self._handle_open_position,
            lambda msg: self._is_admin(msg.from_user.id),
            commands=['open']
        )
        self.dp.register_message_handler(
            self._handle_close_position,
            lambda msg: self._is_admin(msg.from_user.id),
            commands=['close']
        )
        self.dp.register_message_handler(
            self._handle_positions,
            lambda msg: self._is_admin(msg.from_user.id),
            commands=['positions']
        )
        
        # User commands
        self.dp.register_message_handler(
            self._handle_start,
            commands=['start', 'help']
        )
        self.dp.register_message_handler(
            self._handle_balance,
            commands=['balance']
        )
        
        # New Solana handlers
        self.dp.register_message_handler(
            self._handle_check_contract,
            lambda msg: self._is_admin(msg.from_user.id),
            commands=['check']
        )
        self.dp.register_message_handler(
            self._handle_liquidity,
            lambda msg: self._is_admin(msg.from_user.id),
            commands=['liquidity']
        )
        self.dp.register_message_handler(
            self._handle_swap,
            lambda msg: self._is_admin(msg.from_user.id),
            commands=['swap']
        )
    
    def _is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in self.admin_ids
    
    async def _handle_start(self, message: Message) -> None:
        """Handle /start command"""
        help_text = (
            "🤖 Вітаю! Я бот для керування торгівлею.\n\n"
            "Доступні команди:\n"
            "/open TOKEN AMOUNT - Відкрити нову позицію\n"
            "/close ID - Закрити позицію\n"
            "/positions - Показати відкриті позиції\n"
            "/balance - Показати баланс\n"
            "/help - Показати це повідомлення\n\n"
            "❗️ Деякі команди доступні тільки для адміністраторів"
        )
        await message.reply(help_text)
    
    async def _handle_open_position(self, message: Message) -> None:
        """Handle /open command"""
        try:
            # Expected format: /open TOKEN AMOUNT
            _, token, amount = message.text.split()
            amount = float(amount)
            
            # Validate token
            if not await self.trade_validator.validate_token(token):
                await message.reply(f"❌ Помилка: Невідомий токен {token}")
                return
            
            # Get current price
            price = await self.price_calculator.get_price(token)
            if not price:
                await message.reply("❌ Помилка: Не вдалося отримати ціну")
                return
            
            # Open position
            position = await self.position_manager.open_position(token, amount, price)
            
            await message.reply(
                f"✅ Позицію відкрито:\n"
                f"ID: {position.id}\n"
                f"Токен: {position.token}\n"
                f"Кількість: {position.amount}\n"
                f"Ціна: {position.entry_price}"
            )
            
        except ValueError as e:
            await message.reply(f"❌ Помилка: {str(e)}")
        except Exception as e:
            await message.reply("❌ Сталася помилка при відкритті позиції")
    
    async def _handle_close_position(self, message: Message) -> None:
        """Handle /close command"""
        try:
            # Expected format: /close POSITION_ID
            _, position_id = message.text.split()
            position_id = int(position_id)
            
            # Close position
            position = await self.position_manager.close_position(position_id)
            
            await message.reply(
                f"✅ Позицію закрито:\n"
                f"ID: {position.id}\n"
                f"Прибуток: {position.profit}"
            )
            
        except ValueError as e:
            await message.reply(f"❌ Помилка: {str(e)}")
        except Exception as e:
            await message.reply("❌ Сталася помилка при закритті позиції")
    
    async def _handle_positions(self, message: Message) -> None:
        """Handle /positions command"""
        try:
            positions = await self.position_manager.get_positions()
            
            if not positions:
                await message.reply("📊 Немає відкритих позицій")
                return
            
            positions_text = "\n\n".join(
                f"ID: {p.id}\n"
                f"Токен: {p.token}\n"
                f"Кількість: {p.amount}\n"
                f"Ціна входу: {p.entry_price}"
                for p in positions
            )
            
            await message.reply(f"📊 Відкриті позиції:\n\n{positions_text}")
            
        except Exception as e:
            await message.reply("❌ Сталася помилка при отриманні позицій")
    
    async def _handle_balance(self, message: Message) -> None:
        """Handle /balance command"""
        try:
            # TODO: Implement balance checking
            await message.reply("💰 Функція перевірки балансу в розробці")
        except Exception as e:
            await message.reply("❌ Сталася помилка при отриманні балансу")
    
    async def _handle_check_contract(self, message: Message) -> None:
        """Handle /check command"""
        try:
            # Expected format: /check CONTRACT_ADDRESS
            _, contract_address = message.text.split()
            
            contract_info = await self.solana.get_contract_info(contract_address)
            
            if not contract_info:
                await message.reply("❌ Контракт не знайдено")
                return
            
            info_text = (
                f"📄 Інформація про контракт:\n"
                f"Адреса: {contract_info['address']}\n"
                f"Баланс: {contract_info['balance']} SOL\n"
                f"Власник: {contract_info['owner']}\n"
                f"Виконуваний: {'Так' if contract_info['executable'] else 'Ні'}"
            )
            
            await message.reply(info_text)
            
        except ValueError:
            await message.reply("❌ Неправильний формат команди. Використовуйте: /check CONTRACT_ADDRESS")
        except Exception as e:
            await message.reply(f"❌ Помилка: {str(e)}")
    
    async def _handle_liquidity(self, message: Message) -> None:
        """Handle /liquidity command"""
        try:
            # Expected format: /liquidity TOKEN_ADDRESS
            _, token_address = message.text.split()
            
            liquidity = await self.solana.check_liquidity(token_address)
            
            await message.reply(f"💧 Ліквідність: {liquidity} SOL")
            
        except ValueError:
            await message.reply("❌ Неправильний формат команди. Використовуйте: /liquidity TOKEN_ADDRESS")
        except Exception as e:
            await message.reply(f"❌ Помилка: {str(e)}")
    
    async def _handle_swap(self, message: Message) -> None:
        """Handle /swap command"""
        try:
            # Expected format: /swap TOKEN_ADDRESS AMOUNT SLIPPAGE
            _, token_address, amount, slippage = message.text.split()
            amount = float(amount)
            slippage = float(slippage)
            
            result = await self.solana.execute_swap(token_address, amount, slippage)
            
            if result:
                await message.reply(
                    f"✅ Swap виконано:\n"
                    f"Токен: {token_address}\n"
                    f"Кількість: {amount}\n"
                    f"Проковзування: {slippage}%"
                )
            else:
                await message.reply("❌ Не вдалося виконати swap")
            
        except ValueError:
            await message.reply("❌ Неправильний формат команди. Використовуйте: /swap TOKEN_ADDRESS AMOUNT SLIPPAGE")
        except Exception as e:
            await message.reply(f"❌ Помилка: {str(e)}")
    
    async def start(self) -> None:
        """Start the bot"""
        try:
            # Connect to Solana
            if not await self.solana.connect_to_network(self.solana_endpoint):
                print("Failed to connect to Solana network")
                return
            
            await self.dp.start_polling()
        except Exception as e:
            print(f"Error starting bot: {e}")
    
    async def stop(self) -> None:
        """Stop the bot"""
        try:
            await self.dp.stop_polling()
            await self.bot.close()
        except Exception as e:
            print(f"Error stopping bot: {e}")
    
    async def send_message(self, chat_id: int, text: str) -> Optional[Message]:
        """Send message to specified chat"""
        try:
            return await self.bot.send_message(chat_id=chat_id, text=text)
        except Exception as e:
            print(f"Error sending message: {e}")
            return None 