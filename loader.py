import logging

import sentry_sdk
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aioredis import Redis
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

import config
from actions.basket_actions.basket_actions import BasketActions
from actions.category_actions.category_actions import CategoryActions
from actions.product_actions.product_actions import ProductActions

# -------------------------------LOGS-----------------------------------------------

logging.basicConfig(level=logging.INFO)

# -------------------------------DATABASE-------------------------------------------
engine = create_async_engine(
    f"postgresql+asyncpg://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}@localhost/{config.POSTGRES_DB}"
)
async_sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

# -------------------------------AIOGRAM BOT----------------------------------------

# AIOGRAM BOT
bot = Bot(token=config.API_TOKEN)
dp = Dispatcher(bot, storage=RedisStorage2())
redis_cache = Redis(decode_responses=True, db=1)
sentry_sdk.init(
    dsn=config.DSN,

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0
)
# ---------------------------------ACTIONS------------------------------------------
product_actions = ProductActions()
basket_actions = BasketActions()
category_actions = CategoryActions()
