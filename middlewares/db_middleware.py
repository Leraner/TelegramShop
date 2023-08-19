import json

from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import async_sessionmaker

from loader import redis_cache, dp


class DbMiddleware(BaseMiddleware):
    def __init__(self, session_pool: async_sessionmaker):
        super().__init__()
        self.session_pool = session_pool

    async def get_all_useless_messages(self, msg: Message) -> list:
        useless_messages = await redis_cache.get(msg.from_user.username + ':useless_messages')
        if useless_messages is not None:
            await redis_cache.set(msg.from_user.username + ':useless_messages', json.dumps([]))
            return json.loads(useless_messages)
        return []

    async def get_all_useless_basket_messages(self, msg: Message) -> list:
        basket_data = await redis_cache.get(msg.from_user.username + ':basket')
        if basket_data is not None:
            basket_data = json.loads(basket_data)
            messages = basket_data['messages'].copy()
            messages.append(basket_data['tab_message'])
            basket_data['messages'].clear()
            basket_data['tab_message'] = None
            await redis_cache.set(msg.from_user.username + ':basket', json.dumps(basket_data))
            return messages
        return []

    async def get_all_useless_product_messages(self, msg: Message) -> list:
        product_data = await redis_cache.get(msg.from_user.username + ':product')
        if product_data is not None:
            product_data = json.loads(product_data)
            messages = product_data['messages'].copy()
            messages.append(product_data['tab_message'])
            product_data['messages'].clear()
            product_data['tab_message'] = None
            await redis_cache.set(msg.from_user.username + ':product', json.dumps(product_data))
            return messages
        return []

    async def delete_useless_messages(self, msg: Message) -> None:
        useless_messages = await self.get_all_useless_messages(msg)
        useless_messages_basket = await self.get_all_useless_basket_messages(msg)
        useless_messages_product = await self.get_all_useless_product_messages(msg)
        useless_messages = [
            *useless_messages,
            *useless_messages_basket,
            *useless_messages_product
        ]

        for message in useless_messages:
            if message is not None:
                await dp.bot.delete_message(chat_id=msg.chat.id, message_id=message)

    async def on_process_message(self, msg: Message, data: dict) -> None:
        if msg.text is not None:
            if msg.text[0] == '/':
                await self.delete_useless_messages(msg)

        if data['raw_state'] is None:
            await redis_cache.set(msg.from_user.username + ':useless_messages', json.dumps([msg.message_id]))

        async with self.session_pool() as session:
            data['session'] = session

    async def on_process_callback_query(self, call: CallbackQuery, data: dict) -> None:
        if data.get('callback_data') is not None:
            async with self.session_pool() as session:
                data['session'] = session
