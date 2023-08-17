from actions.user_actions import UserActions
from exceptions.exceptions import PermissionDenied


class Actions:
    pagination_class = None

    @staticmethod
    def check_permission(permission_class):
        def bar(func):
            async def wrapper(*args, **kwargs):
                username = kwargs.get('username')
                if permission_class is not None:
                    user = await UserActions.get_user_by_username(username=username, session=kwargs.get('session'))
                    if permission_class.permission(user):
                        return await func(*args, **kwargs)
                    else:
                        raise PermissionDenied()

            return wrapper

        return bar

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
