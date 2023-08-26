from aiogram import types
from sqlalchemy.ext.asyncio import AsyncSession

from database import UserDAL, User


class UserActions:
    """User actions class"""

    @staticmethod
    async def create_new_user(message: types.Message, session: AsyncSession) -> User:
        async with session.begin():
            user_dal = UserDAL(session=session)
            new_user = await user_dal.add_user(dict(message))
        return new_user

    @staticmethod
    async def get_user_by_username(username: str, session: AsyncSession) -> User:
        async with session.begin():
            user_dal = UserDAL(session=session)
            user = await user_dal.get_user_by_username(username)
        return user
