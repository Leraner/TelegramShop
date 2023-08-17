from aiogram.dispatcher.middlewares import BaseMiddleware, LifetimeControllerMiddleware
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import async_sessionmaker


class DbMiddleware(BaseMiddleware):
    def __init__(self, session_pool: async_sessionmaker):
        super().__init__()
        self.session_pool = session_pool

    async def on_process_message(self, msg: Message, data: dict) -> None:
        async with self.session_pool() as session:
            data['session'] = session

    async def on_process_callback_query(self, call: CallbackQuery, data: dict) -> None:
        if data.get('callback_data') is not None:
            async with self.session_pool() as session:
                data['session'] = session
