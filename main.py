import asyncio
from config import config, register_routers
from aiogram import Bot, Dispatcher
from Database.db import check_db


async def main():
    await check_db()
    bot = Bot(token=config.bot_token)
    dp = Dispatcher()
    register_routers(dp)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
