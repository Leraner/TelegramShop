import asyncio
import datetime

from sqlalchemy import Column, String, Integer, Text, Date, Boolean, ForeignKey, Table, event
from sqlalchemy.orm import DeclarativeBase, relationship, backref

from loader import elastic_search_client


class Base(DeclarativeBase):
    pass


# Association table for "many to many" relationships basket and product
association_basket_table = Table(
    'association_table',
    Base.metadata,
    Column('basket_id', ForeignKey('Basket.basket_id')),
    Column('product_id', ForeignKey('Product.product_id'))
)


class Category(Base):
    """Category model"""
    __tablename__ = 'Category'

    category_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String(150), nullable=False)
    product = relationship('Product', backref=backref('Category'))

    def __repr__(self):
        return f'<Category (id={self.category_id}, name={self.name}>, description={self.description})>'


class Basket(Base):
    """Basket model"""
    __tablename__ = 'Basket'

    basket_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('User.user_id'))
    products = relationship('Product', secondary=association_basket_table, backref=backref('Basket'))

    def __repr__(self):
        return f'<Basket (id={self.basket_id}, user_id={self.user_id})>'


class User(Base):
    """User model"""
    __tablename__ = 'User'

    user_id = Column(Integer, primary_key=True)
    username = Column(String(15), nullable=False)
    first_name = Column(String(30), nullable=True)
    last_name = Column(String(30), nullable=True)
    is_admin = Column(Boolean, default=False)
    basket = relationship('Basket', uselist=False, backref=backref('User'))

    def __repr__(self) -> str:
        return f'<User(id={self.user_id}, username={self.username}, first_name={self.first_name}, last_name={self.last_name})>'


class Product(Base):
    """Product model"""
    __tablename__ = 'Product'

    product_id = Column(Integer, primary_key=True)
    name = Column(String(35), nullable=False)
    image_path = Column(String, default='media/Box.png', nullable=False)
    description = Column(Text, nullable=False)
    created_date = Column(Date, default=datetime.datetime.utcnow(), nullable=False)
    category_id = Column(Integer, ForeignKey('Category.category_id'), nullable=False)

    def __repr__(self):
        return f'<Product(id={self.product_id}, name={self.name}, description={self.description}, created_date={self.created_date})>'


@event.listens_for(Product, 'after_insert')
def create_product_in_elastic(mapper, connection, target):
    """On creating model in database create product in elasticsearch index"""
    asyncio.create_task(elastic_search_client.create_elastic_product(product=target))
