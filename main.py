import asyncio

from config import config, register_routers
from aiogram import Bot, Dispatcher, F
from Database.db import check_db


async def main():
    await check_db()
    bot = Bot(token=config.bot_token.get_secret_value())
    dp = Dispatcher()
    register_routers(dp)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())

