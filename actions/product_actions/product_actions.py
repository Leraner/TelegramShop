from sqlalchemy.ext.asyncio import AsyncSession

from actions.actions import Actions
from actions.product_actions.pagination import ProductPagination
from database import Product, ProductDAL, User
from permissions import PermissionAdmin
from serializers import ProductSerializer


class ProductActions(Actions):
    """Product actions class"""
    pagination_class = ProductPagination
    serializer_class = ProductSerializer

    async def get_all_products(self, session: AsyncSession) -> list[list[dict]]:
        async with session.begin():
            product_dal = ProductDAL(session=session)
            products = await product_dal.get_all_products()
            return await self.paginated_objects(await self.serialize(products))

    @Actions.check_permission(permission_class=PermissionAdmin)
    async def create_product(self, data: dict, session: AsyncSession, user: User) -> Product:
        """
        This method for create a product and check user's permissions
        user - (User instance) - needs for checking user's permissions
        """
        async with session.begin():
            product_dal = ProductDAL(session=session)
            new_product = await product_dal.create_product(data=await self.validate(data))
            return new_product

    async def get_product_by_id(self, product_id: int, session: AsyncSession) -> Product:
        async with session.begin():
            product_dal = ProductDAL(session=session)
            product = await product_dal.get_product_by_id(product_id=product_id)
            return product
