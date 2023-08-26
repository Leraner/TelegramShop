import logging

from sqlalchemy.ext.asyncio import async_sessionmaker

from database import Category


class CategoryCommand:
    """Prepare stand category class"""

    @staticmethod
    async def prepare_stand_categories(session_pool: async_sessionmaker):
        """Creating categories in the database before starting bot"""
        categories = [
            {'name': 'Товары на лето', 'description': 'Категория товаров на лето'},
            {'name': 'Товары для детей', 'description': 'Категория товаров для детей'},
            {'name': 'Кроссовки', 'description': 'Категория товаров связанных с кроссовками'}
        ]

        async with session_pool() as session:
            async with session.begin():
                for category in categories:
                    new_category = Category(
                        name=category['name'],
                        description=category['description']
                    )
                    session.add(new_category)
                    await session.flush()
                    logging.info(f'CREATED CATEGORY {new_category}')
