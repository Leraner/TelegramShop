import logging

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

import config
from actions.product_actions import ProductActions

logging.basicConfig(level=logging.INFO)

# DATABASE

engine = create_async_engine(
    f"postgresql+asyncpg://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}@localhost/{config.POSTGRES_DB}"
)
async_sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

# ---------------------------------------------------------------------------

# AIOGRAM BOT
bot = Bot(token=config.API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# ---------------------------------------------------------------------------

product_actions = ProductActions()
