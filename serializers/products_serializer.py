from pydantic import BaseModel


class ProductSerializer(BaseModel):
    product_id: int
    name: str
    description: str
    image_path: str
