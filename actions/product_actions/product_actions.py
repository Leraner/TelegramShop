from sqlalchemy.ext.asyncio import AsyncSession

from actions.actions import Actions
from actions.product_actions.pagination import ProductPagination
from database.dals import ProductDAL
from database.models import Product
from permissions.product_permissions import PermissionAdmin
from serializers.products_serializer import ProductSerializer


class ProductActions(Actions):
    pagination_class = ProductPagination
    serializer_class = ProductSerializer

    async def show_products(self, session: AsyncSession) -> list[list[dict]]:
        async with session.begin():
            product_dal = ProductDAL(session=session)
            products = await product_dal.get_all_products()
            return await self.paginated_objects(await self.serialize(products))

    @Actions.check_permission(permission_class=PermissionAdmin)
    async def create_product(self, message: dict, session: AsyncSession, username: str) -> Product:
        """
        This method for create a product and check user's permissions
        :param message: dict
        :param session: AsyncSession
        :param username: str - needs for checking user's permissions
        :return: Product
        """
        async with session.begin():
            product_dal = ProductDAL(session=session)
            new_product = await product_dal.create_product(message=message)
            return new_product

    async def get_product_by_id(self, product_id: int, session: AsyncSession):
        async with session.begin():
            product_dal = ProductDAL(session=session)
            product = await product_dal.get_product_by_id(product_id=product_id)
            return product
