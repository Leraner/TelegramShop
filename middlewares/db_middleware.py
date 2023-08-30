import json
import logging

from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import async_sessionmaker

from loader import redis_cache, dp


class DbMiddleware(BaseMiddleware):
    def __init__(self, session_pool: async_sessionmaker) -> None:
        super().__init__()
        self.session_pool = session_pool

    async def get_all_useless_messages(self, msg: Message) -> list:
        """Return the messages that were sent during the all commands"""
        useless_messages = await redis_cache.get(msg.from_user.username + ':useless_messages')
        if useless_messages is not None:
            await redis_cache.set(msg.from_user.username + ':useless_messages', json.dumps([]))
            logging.info(f'RECEIVED ALL useless_messages IN {msg.from_user.username} CHAT FROM CACHE')
            return json.loads(useless_messages)
        return []

    async def delete_useless_messages(self, msg: Message) -> None:
        """Delete messages when user send another command"""
        useless_messages = await self.get_all_useless_messages(msg)

        for message in set(useless_messages):
            if message is not None:
                await dp.bot.delete_message(chat_id=msg.chat.id, message_id=message, for_cache=True)
                logging.info(f'DELETED MESSAGE {message} FROM {msg.from_user.username} CHAT')

    async def add_useless_messages_with_state(self, msg: Message) -> None:
        """This method add user's messages into cache with key - :useless_messages"""
        data_messages = await redis_cache.get(msg.from_user.username + ':useless_messages')
        if data_messages is not None:
            data_messages = json.loads(data_messages)
            data_messages.append(msg.message_id)
            await redis_cache.set(msg.from_user.username + ':useless_messages', json.dumps(data_messages))
        else:
            data_messages = []
            data_messages.append(msg.message_id)
            await redis_cache.set(msg.from_user.username + ':useless_messages', json.dumps(data_messages))
        logging.info(f'USER {msg.from_user.username} CHAT MESSAGE {msg.message_id} ADDED INTO CACHE')

    async def on_process_message(self, msg: Message, data: dict) -> None:
        if msg.text is not None and data['raw_state'] is None:
            if msg.text[0] == '/':
                await self.delete_useless_messages(msg)

        await self.add_useless_messages_with_state(msg=msg)

        async with self.session_pool() as session:
            data['session'] = session

    async def on_process_callback_query(self, call: CallbackQuery, data: dict) -> None:
        if data.get('callback_data') is not None:
            async with self.session_pool() as session:
                data['session'] = session
