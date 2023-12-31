import datetime

from pydantic import BaseModel


class BasketProductsSerializer(BaseModel):
    product_id: int
    name: str
    description: str
    image_path: str
    created_date: datetime.datetime
