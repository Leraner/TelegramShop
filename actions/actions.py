from pydantic import ValidationError

from exceptions.exceptions import PermissionDenied, SerializerValidationError, SerializerNotFound


class Actions:
    """Base Action class"""
    pagination_class = None
    serializer_class = None

    @staticmethod
    def check_permission(permission_class):
        def bar(func):
            async def wrapper(*args, **kwargs):
                if permission_class is not None:
                    if permission_class.permission(kwargs.get('user')):
                        return await func(*args, **kwargs)
                    else:
                        raise PermissionDenied()

            return wrapper

        return bar

    @classmethod
    async def serialize(cls, objects) -> list:
        if cls.serializer_class is None:
            raise SerializerNotFound()
        new_objects_list = []
        for object in objects:
            try:
                new_objects_list.append(cls.serializer_class(**object.__dict__).dict())
            except ValidationError as error:
                field = str(error).split('Field')[0]
                raise SerializerValidationError(field)
        return new_objects_list

    @classmethod
    async def validate(cls, object) -> dict:
        if cls.serializer_class is None:
            raise SerializerNotFound()
        new_object = dict(cls.serializer_class(**object))
        new_data = {}
        for field in new_object.copy():
            if new_object[field] is not None:
                new_data.update({field: new_object[field]})
        return new_data

    @classmethod
    def paginate(cls, objects) -> list:
        for i in range(0, len(objects), cls.pagination_class.max_items):
            yield objects[i:i + cls.pagination_class.max_items]

    @classmethod
    async def paginated_objects(cls, objects) -> list[list]:
        if cls.pagination_class is not None:
            paginated_products = list(cls.paginate(objects))
            return paginated_products
        return objects


class ElasticSearchActions(Actions):
    """ElasticSearch Action class"""
    serializer_class = None
    pagination_class = None

    @classmethod
    async def serialize(cls, objects) -> list:
        if cls.serializer_class is None:
            raise SerializerNotFound()
        new_objects_list = []
        for object in objects:
            try:
                new_objects_list.append(cls.serializer_class(**object['_source']).dict())
            except ValidationError as error:
                field = str(error).split('Field')[0]
                raise SerializerValidationError(field)
        return new_objects_list
