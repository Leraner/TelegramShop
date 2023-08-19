import json

from aiogram import types
from sqlalchemy.ext.asyncio import AsyncSession

from actions.user_actions.user_actions import UserActions
from loader import dp, redis_cache


@dp.message_handler(commands=['start'])
async def start_command(message: types.Message, session: AsyncSession) -> None:
    bot_data = await dp.bot.get_me()
    user = await UserActions.get_user_by_username(username=message.from_user.username, session=session)
    if not user:
        new_user = await UserActions.create_new_user(message=message, session=session)
        msg = await message.answer(f'Hello, {new_user.first_name}, welcome to {bot_data["username"]}')
        useless_messages = json.loads(await redis_cache.get(message.from_user.username + ':useless_messages'))
        useless_messages.append(msg.message_id)
        await redis_cache.set(message.from_user.username + ':useless_messages', json.loads(useless_messages))
