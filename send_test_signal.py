from telethon import TelegramClient
import asyncio

async def main():
    client = TelegramClient('test_session', '28533006', '4e03193ba06e0d9d4d8e6f3ad9e51e1f')
    await client.start()
    await client.send_message('@testttggjb', '2zMMhcVQEXDtdE6vsFS7S7D5oUodfJHE8vd1gnBouauv')
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main()) 