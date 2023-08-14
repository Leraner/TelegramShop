from aiogram import executor

from handlers import dp
from loader import async_sessionmaker
from middlewares.db_middleware import DbMiddleware


async def on_startup(dp):
    # RuntimeWarning - without that it doesn't work
    # dp.bot.set_my_commands([
    #     types.BotCommand("start", "Запустить бота"),
    #     types.BotCommand("create_product", "Создать продукт"),
    # ])
    dp.middleware.setup(DbMiddleware(session_pool=async_sessionmaker))


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)
