import asyncio

from sqlalchemy import event

from database.models import Product
from loader import elastic_search_client


@event.listens_for(Product, 'after_insert')
def create_product_in_elastic(mapper, connection, target):
    """On creating model in database create product in elasticsearch index"""
    asyncio.create_task(elastic_search_client.create_elastic_product(product=target))
