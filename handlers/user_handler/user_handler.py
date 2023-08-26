from aiogram import types
from sqlalchemy.ext.asyncio import AsyncSession

from actions import user_actions
from keyboards.inline_keyboard import InlineKeyboard
from loader import dp


@dp.message_handler(commands=['start'])
async def start_command(message: types.Message, session: AsyncSession) -> None:
    """
    User start command

    If user is admin, command will add additional buttons for user
    """
    bot_data = await dp.bot.get_me()
    user = await user_actions.get_user_by_username(username=message.from_user.username, session=session)
    if not user:
        new_user = await user_actions.create_new_user(message=message, session=session)
        await message.answer(
            f'Hello, {new_user.first_name}, welcome to {bot_data["username"]}',
            reply_markup=await InlineKeyboard.generate_commands_reply_keyboard_markup()
        )
    else:
        if user.is_admin:
            msg = await message.answer(
                'Вам доступны новые функции',
                reply_markup=await InlineKeyboard.generate_commands_reply_keyboard_markup(user_is_admin=True)
            )
