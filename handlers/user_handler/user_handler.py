from aiogram import types
from sqlalchemy.ext.asyncio import AsyncSession

from actions.user_actions.user_actions import UserActions
from keyboards.inline_keyboard import InlineKeyboard
from loader import dp


@dp.message_handler(commands=['start'])
async def start_command(message: types.Message, session: AsyncSession) -> None:
    bot_data = await dp.bot.get_me()
    user = await UserActions.get_user_by_username(username=message.from_user.username, session=session)
    if not user:
        new_user = await UserActions.create_new_user(message=message, session=session)
        await message.answer(
            f'Hello, {new_user.first_name}, welcome to {bot_data["username"]}',
            reply_markup=await InlineKeyboard.generate_reply_keyboard_markup()
        )
    else:
        if user.is_admin:
            msg = await message.answer(
                'Вам доступны новые функции',
                reply_markup=await InlineKeyboard.generate_reply_keyboard_markup(user_is_admin=True)
            )
