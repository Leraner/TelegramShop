from sqlalchemy.ext.asyncio import AsyncSession

from database.dals import BasketDAL
from database.models import Basket, Product, User


class BasketActions:

    @staticmethod
    async def create_new_basket() -> Basket:
        new_basket = await BasketDAL.create_basket()
        return new_basket

    @staticmethod
    async def add_product_to_user_basket(user: User, product: Product, session: AsyncSession) -> User:
        async with session.begin():
            basket_dal = BasketDAL(session=session)
            new_basket_with_products = await basket_dal.add_product_to_basket(user=user, product=product)
            user.basket = new_basket_with_products
            return user
