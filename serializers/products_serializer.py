from pydantic import BaseModel


class ProductSerializer(BaseModel):
    name: str
    description: str
    image_path: str
