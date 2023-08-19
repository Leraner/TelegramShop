from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from actions.actions import Actions
from actions.basket_actions.pagination import BasketPagination
from database.dals import BasketDAL
from database.models import Basket, Product, User
from serializers.basket_serializer import BasketProductsSerializer


class BasketActions(Actions):
    pagination_class = BasketPagination
    serializer_class = BasketProductsSerializer

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

    @staticmethod
    async def remove_product_from_basket(user: User, product: Product, session: AsyncSession) -> User:
        async with session.begin():
            basket_dal = BasketDAL(session=session)
            new_basket_without_product = await basket_dal.remove_product_from_basket(user=user, product=product)
            user.basket = new_basket_without_product
            return user

    async def get_user_basket(self, user_id: int, session: AsyncSession) -> Optional[list[list[dict]]]:
        async with session.begin():
            basket_dal = BasketDAL(session=session)
            user_basket_products = await basket_dal.get_user_basket(user_id=user_id)
            if user_basket_products is None:
                return None

            return await self.paginated_objects(await self.serialize(user_basket_products))
