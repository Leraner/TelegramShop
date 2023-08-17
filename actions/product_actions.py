from sqlalchemy.ext.asyncio import AsyncSession

from actions.actions import Actions
from actions.pagination import ProductPagination
from database.dals import ProductDAL
from database.models import Product
from permissions.product_permissions import PermissionAdmin


class ProductActions(Actions):
    pagination_class = ProductPagination

    async def show_products(self, session: AsyncSession) -> list[Product]:
        async with session.begin():
            product_dal = ProductDAL(session=session)
            products = await product_dal.get_all_products()
            return await self.paginated_objects(products)

    @Actions.check_permission(permission_class=PermissionAdmin)
    async def create_product(self, message: dict, session: AsyncSession, username: str) -> Product:
        async with session.begin():
            product_dal = ProductDAL(session=session)
            new_product = await product_dal.create_product(message=message)
            return new_product

    async def get_product_by_id(self, product_id: int, session: AsyncSession):
        async with session.begin():
            product_dal = ProductDAL(session=session)
            product = await product_dal.get_product_by_id(product_id=product_id)
            return product
