import logging

import sentry_sdk
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aioredis import Redis
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

import config
from bot import CustomBotClient
from search.search import ElasticSearchClient

# -------------------------------LOGS-----------------------------------------------

logging.basicConfig(level=logging.INFO)

# -------------------------------DATABASE-------------------------------------------
engine = create_async_engine(
    f"postgresql+asyncpg://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}@localhost/{config.POSTGRES_DB}"
)
async_sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

# -------------------------------AIOGRAM BOT----------------------------------------

# AIOGRAM BOT
redis_cache = Redis(decode_responses=True, db=1)
bot = CustomBotClient(token=config.API_TOKEN, redis_cache=redis_cache)
# dp = Dispatcher(bot, storage=RedisStorage2())
dp = Dispatcher(bot, storage=MemoryStorage())
sentry_sdk.init(
    dsn=config.DSN,

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0
)
elastic_search_client = ElasticSearchClient(
    indices=config.ELASTIC_INDICES,
    elastic_hosts=config.elastic_hosts
)
