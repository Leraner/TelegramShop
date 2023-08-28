""" Point of entry """

from aiogram import executor, Dispatcher

from handlers import dp
from loader import async_sessionmaker, elastic_search_client
from middlewares.db_middleware import DbMiddleware
from management.prepare_stand_categories import CategoryCommand


async def on_startup(dp: Dispatcher):
    # RuntimeWarning - without that it doesn't work
    # dp.bot.set_my_commands([
    #     types.BotCommand("start", "Запустить бота"),
    #     types.BotCommand("create_product", "Создать продукт"),
    # ])
    # For production
    # await CategoryCommand.prepare_stand_categories(session_pool=async_sessionmaker)
    dp.middleware.setup(DbMiddleware(session_pool=async_sessionmaker))
    await elastic_search_client.create_index()


async def on_shutdown(dp: Dispatcher):
    await dp.storage.close()


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown)
