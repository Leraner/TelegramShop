from pydantic import BaseModel, field_validator

from exceptions.exceptions import SerializerValidationError


class ProductSerializer(BaseModel):
    product_id: int = None
    name: str
    description: str
    image_path: str
    category_id: int

    @field_validator('name', 'description')
    @classmethod
    def validate(cls, field: str) -> str:
        if field.startswith('/'):
            raise SerializerValidationError(
                message=f'Validation error: incorrect data in {field} field'
            )
        else:
            return field
