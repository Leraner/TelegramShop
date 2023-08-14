import datetime

from sqlalchemy import Column, String, Integer, Text, Date, Boolean, ForeignKey, Table
from sqlalchemy.orm import DeclarativeBase, relationship, backref


class Base(DeclarativeBase):
    pass


"""
Create basket
Create categories
Implement message deletion after action
"""

association_basket_table = Table(
    'association_table',
    Base.metadata,
    Column('basket_id', ForeignKey('Basket.basket_id')),
    Column('product_id', ForeignKey('Product.product_id'))
)


class Basket(Base):
    __tablename__ = 'Basket'

    basket_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('User.user_id'))
    products = relationship('Product', secondary=association_basket_table, backref=backref('Basket'))

    def __repr__(self):
        return f'<Basket (id={self.basket_id}, user_id={self.user_id})>'


class User(Base):
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
    __tablename__ = 'Product'

    product_id = Column(Integer, primary_key=True)
    name = Column(String(35), nullable=False)
    image_path = Column(String, default='media/Box.png', nullable=False)
    description = Column(Text, nullable=False)
    created_date = Column(Date, default=datetime.datetime.utcnow(), nullable=False)

    def __repr__(self):
        return f'<Product(id={self.product_id}, name={self.name}, description={self.description}, created_date={self.created_date})>'
