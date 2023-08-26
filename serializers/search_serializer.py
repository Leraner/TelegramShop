from pydantic import BaseModel


class SearchSerializerProduct(BaseModel):
    product_id: int = None
    name: str
    description: str
    image_path: str
    category_id: int
