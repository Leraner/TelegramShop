from aiogram import types
from sqlalchemy.ext.asyncio import AsyncSession

from actions.basket_actions import BasketActions
from database.dals import UserDAL
from database.models import User


class UserActions:
    @staticmethod
    async def create_new_user(message: types.Message, session: AsyncSession) -> User:
        async with session.begin():
            user_dal = UserDAL(session=session)
            new_user = await user_dal.add_user(dict(message), await BasketActions.create_new_basket())
        return new_user

    @staticmethod
    async def get_user_by_username(username: str, session: AsyncSession) -> User:
        async with session.begin():
            user_dal = UserDAL(session=session)
            user = await user_dal.get_user_by_username(username)
        return user
