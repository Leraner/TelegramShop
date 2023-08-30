import logging
from typing import Union, Any, Sequence

from sqlalchemy import select, Row, RowMapping
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import User, Product, Basket, Category


class CategoryDAL:
    """Data Access Layer for operating category info"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all_categories(self) -> Sequence[Union[Union[Row, RowMapping], Any]]:
        query = select(Category)
        result = await self.session.execute(query)
        categories = result.scalars().all()
        logging.info(f'RECEIVED ALL CATEGORIES')
        return categories

    async def create_new_category(self, data: dict) -> Category:
        new_category = Category(**data)
        self.session.add(new_category)
        await self.session.flush()
        logging.info(f'CREATED NEW CATEGORY {new_category}')
        return new_category


class BasketDAL:
    """Data Access Layer for operating basket info"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    async def create_basket() -> Basket:
        new_basket = Basket()
        return new_basket

    async def remove_product_from_basket(self, user: User, product: Product) -> Basket:
        basket = user.basket
        basket.products.remove(product)
        self.session.add(basket)
        await self.session.flush()
        logging.info(f'REMOVED {product} FROM {basket}')
        return basket

    async def add_product_to_basket(self, user: User, product: Product) -> Basket:
        basket = user.basket
        basket.products.append(product)
        self.session.add(basket)
        await self.session.flush()
        logging.info(f'ADDED {product} INTO {basket}')
        return basket

    async def get_user_basket(self, user_id: int) -> list[Product]:
        query = select(Basket).where(Basket.user_id == user_id)
        result = await self.session.execute(query)
        products = result.fetchone()
        if products is not None:
            logging.info(f'RECEIVED USER BASKET BY USER_ID - {user_id}')
            return products[0].products


class UserDAL:
    """Data Access Layer for operating user info"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_user(self, message: dict) -> User:
        basket = await BasketDAL.create_basket()
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
            logging.info(f'RECEIVED USER {user_rows[0]}, BY USERNAME {username}')
            return user_rows[0]


class ProductDAL:
    """Data Access Layer for operating product info"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_product(self, data: dict) -> Product:
        new_product = Product(**data)
        self.session.add(new_product)
        await self.session.flush()
        logging.info(f'CREATED NEW {new_product}')
        return new_product

    async def get_all_products(self) -> Sequence[Union[Union[Row, RowMapping], Any]]:
        query = select(Product)
        result = await self.session.execute(query)
        products = result.scalars().all()
        logging.info("RECEIVED ALL PRODUCTS")
        return products

    async def get_product_by_id(self, product_id: int) -> Product:
        query = select(Product).where(Product.product_id == product_id)
        result = await self.session.execute(query)
        product_rows = result.fetchone()
        if product_rows is not None:
            logging.info(f'RECEIVED PRODUCT: {product_rows[0]}, BY PRODUCT_ID - {product_id}')
            return product_rows[0]
