from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import Message
from sqlalchemy.ext.asyncio import async_sessionmaker


class DbMiddleware(BaseMiddleware):
    def __init__(self, session_pool: async_sessionmaker):
        super().__init__()
        self.session_pool = session_pool

    async def on_process_message(self, msg: Message, data: dict) -> None:
        async with self.session_pool() as session:
            data['session'] = session
