from sqlalchemy.ext.asyncio import AsyncSession

from actions.actions import Actions
from database import CategoryDAL
from serializers import CategorySerializer


class CategoryActions(Actions):
    """Category action class"""
    serializer_class = CategorySerializer

    async def get_all_categories(self, session: AsyncSession) -> list[dict]:
        async with session.begin():
            category_dal = CategoryDAL(session=session)
            categories = await category_dal.get_all_categories()
            return await self.serialize(categories)

    async def create_category(self, data: dict, session: AsyncSession):
        async with session.begin():
            category_dal = CategoryDAL(session=session)
            new_category = await category_dal.create_new_category(data=data)
            return new_category
