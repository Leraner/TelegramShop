import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import User, Product, Basket


class BasketDAL:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    async def create_basket() -> Basket:
        new_basket = Basket()
        return new_basket

    async def add_product_to_basket(self, user: User, product: Product) -> Basket:
        basket = user.basket
        basket.products.append(product)
        self.session.add(basket)
        await self.session.flush()
        logging.info(f'ADDED {product} INTO {basket}')
        return basket


class UserDAL:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_user(self, message: dict, basket) -> User:
        new_user = User(
            username=message['chat'].get('username'),
            first_name=message['chat'].get('first_name'),
            last_name=message['chat'].get('last_name'),
            basket=basket
        )
        self.session.add_all([basket, new_user])
        await self.session.flush()
        logging.info(f'CREATED NEW {new_user} WITH {basket}')
        return new_user

    async def get_user_by_username(self, username: str) -> User:
        query = select(User). \
            where(User.username == username). \
            options(selectinload(User.basket).selectinload(Basket.products))
        result = await self.session.execute(query)
        user_rows = result.fetchone()
        if user_rows is not None:
            return user_rows[0]


class ProductDAL:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_product(self, message: dict) -> Product:
        new_product = Product(**message)
        self.session.add(new_product)
        await self.session.flush()
        logging.info(f'CREATED NEW {new_product}')
        return new_product

    async def get_all_products(self) -> list[Product]:
        query = select(Product)
        result = await self.session.execute(query)
        products = result.scalars().all()
        return products

    async def get_product_by_id(self, product_id: int) -> Product:
        query = select(Product).where(Product.product_id == product_id)
        result = await self.session.execute(query)
        product_rows = result.fetchone()
        if product_rows is not None:
            return product_rows[0]
