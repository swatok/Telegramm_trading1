"""
Головний модуль бота для торгівлі на основі сигналів з Telegram
"""

import os
import json
import asyncio
from datetime import datetime
from telethon import TelegramClient, events
from dotenv import load_dotenv
from loguru import logger

from message_parser import MessageParser
from trading import TradingExecutor
from config import setup_logging
from model.channel import Channel

# Налаштовуємо логування
setup_logging()

class TradingBot:
    def __init__(self):
        # Завантажуємо змінні середовища
        load_dotenv()
        
        # Отримуємо налаштування з .env
        self.api_id = int(os.getenv('TELEGRAM_API_ID'))
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.phone = os.getenv('TELEGRAM_PHONE')
        self.session_name = 'telegram_session'  # Фіксована назва сесії
        
        # Отримуємо список каналів
        channels_json = os.getenv('SOURCE_CHANNELS', '["@mad_apes_gambles", "@testttggjb"]')
        channel_names = json.loads(channels_json)
        
        # Створюємо об'єкти каналів
        self.channels = [
            Channel(
                id=i,
                name=name,
                type='telegram',
                status='active'
            )
            for i, name in enumerate(channel_names)
        ]
        
        self.monitor_channel_id = int(os.getenv('MONITOR_CHANNEL_ID'))
        
        logger.info(
            f"TradingBot ініціалізовано:\n"
            f"- Канали для моніторингу: {[ch.name for ch in self.channels]}\n"
            f"- Канал для логів: {self.monitor_channel_id}"
        )
        
        # Ініціалізуємо компоненти
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        self.message_parser = MessageParser()
        self.trading_executor = TradingExecutor()
        
    async def start(self):
        """Запуск бота"""
        try:
            # Запускаємо клієнт з телефоном
            await self.client.start(phone=self.phone)
            
            # Перевіряємо підключення до каналів
            me = await self.client.get_me()
            logger.info(f"Бот запущено як: {me.username}")
            
            # Перевіряємо доступ до каналів
            for channel in self.channels:
                try:
                    entity = await self.client.get_entity(channel.name)
                    channel.settings['entity_id'] = entity.id
                    logger.info(f"Успішно підключено до каналу {channel.name} (ID: {entity.id})")
                except Exception as e:
                    logger.error(f"Помилка підключення до каналу {channel.name}: {e}")
                    channel.status = 'disabled'
                    channel.add_error("Помилка підключення", {"error": str(e)})
            
            # Відправляємо повідомлення про запуск
            try:
                await self.client.send_message(
                    self.monitor_channel_id,
                    "🟢 Бот запущено та готовий до роботи\n"
                    f"📊 Моніторинг каналів: {len([c for c in self.channels if c.is_active])}"
                )
                logger.info("Відправлено повідомлення про запуск")
            except Exception as e:
                logger.error(f"Помилка відпр��вки повідомлення про запуск: {e}")
            
            # Ініціалізуємо trading executor
            await self.trading_executor.start(self.client)
            
            # Додаємо обробник повідомлень
            @self.client.on(events.NewMessage(chats=[ch.name for ch in self.channels if ch.is_active]))
            async def handle_new_message(event):
                try:
                    message = event.message.text
                    channel_id = event.message.chat_id
                    message_id = event.message.id
                    
                    # Знаходимо канал (враховуємо можливий префікс -1002)
                    channel = next(
                        (ch for ch in self.channels 
                         if ch.settings.get('entity_id') == abs(channel_id) or
                            ch.settings.get('entity_id') == abs(channel_id) % 1000000000000),
                        None
                    )
                    
                    if not channel:
                        logger.warning(f"Отримано повідомлення з невідомого каналу: {channel_id}")
                        return
                        
                    logger.info(f"Отримано нове повідомлення з {channel.name}:\n{message}")
                    
                    # Парсимо повідомлення
                    signal = self.message_parser.parse_message(
                        message,
                        message_id=message_id,
                        channel_id=abs(channel_id)
                    )
                    
                    if signal:
                        logger.info(f"Знайдено торговий сигнал: {signal}")
                        
                        # Додаємо сигнал в історію каналу
                        channel.add_to_history({
                            "token": signal.token.to_dict() if signal.token else {"address": signal.token_address},
                            "action": signal.action,
                            "amount_sol": str(signal.amount_sol) if signal.amount_sol else "0.1",
                            "confidence": str(signal.confidence_score)
                        })
                        
                        # Виконуємо торгову операцію
                        await self.trading_executor.handle_trade_signal(signal)
                    
                except Exception as e:
                    logger.error(f"Помилка обробки повідомлення: {e}", exc_info=True)
                    if channel:
                        channel.add_error("Помилка обробки повідомлення", {"error": str(e)})
            
            # Запускаємо бота
            await self.client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"Помилка запуску бота: {e}", exc_info=True)
            raise
            
    async def stop(self):
        """Зупинка бота"""
        try:
            # Зупиняємо trading executor
            await self.trading_executor.stop()
            
            # Очищуємо ресурси
            await self.trading_executor.cleanup()
            
            # Зупиняємо клієнт
            await self.client.disconnect()
            
            # Оновлюємо статус каналів
            for channel in self.channels:
                channel.status = 'disabled'
            
            logger.info("Бот успішно зупинено")
            
        except Exception as e:
            logger.error(f"Помілка зупинки бота: {e}", exc_info=True)

async def main():
    bot = None
    try:
        bot = TradingBot()
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Отримано сигнал зупинки")
        if bot:
            await bot.stop()
    except Exception as e:
        logger.error(f"Критична помилка: {e}", exc_info=True)
        if bot:
            await bot.stop()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот зупинено користувачем")
    except Exception as e:
        logger.error(f"Критична помилка: {e}", exc_info=True) 