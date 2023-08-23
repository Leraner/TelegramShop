from pydantic import BaseModel


class CategorySerializer(BaseModel):
    category_id: int
    name: str
    description: str
