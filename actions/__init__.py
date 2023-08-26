from .user_actions.user_actions import UserActions
from .product_actions.product_actions import ProductActions
from .category_actions.category_actions import CategoryActions
from .basket_actions.basket_actions import BasketActions

user_actions = UserActions()
product_actions = ProductActions()
basket_actions = BasketActions()
category_actions = CategoryActions()

__all__ = ["user_actions", "product_actions", "category_actions", "basket_actions"]
