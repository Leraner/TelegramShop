from pydantic import BaseModel, field_validator

from exceptions.exceptions import SerializerValidationError


class ProductSerializer(BaseModel):
    product_id: int = None
    name: str
    description: str
    image_path: str
    category_id: int

    @field_validator('name')
    @classmethod
    def name_validator(cls, field: str) -> str:
        if len(field) > 150:
            raise SerializerValidationError(
                message='Maximum number of characters 150'
            )

        if field.startswith('/'):
            raise SerializerValidationError(
                message=f'Validation error: incorrect data {field}'
            )
        else:
            return field

    @field_validator('description')
    @classmethod
    def description_validator(cls, field: str) -> str:
        if field.startswith('/'):
            raise SerializerValidationError(
                message=f'Validation error: incorrect data {field}'
            )
        else:
            return field
