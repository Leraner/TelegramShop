import json
from itertools import zip_longest
from typing import Optional

from aiogram.types import InputMediaPhoto

from database.models import Product
from loader import redis_cache


class ProductPages:
    def __init__(self, products: list = None):
        self.products = products

    async def clear_useless_messages(self, request_forms: dict, data: dict):
        messages_for_delete = set(request_forms['delete'])
        return [item for item in data['messages'] if item not in messages_for_delete]

    async def form_post_data(self, product: Product, request_forms: dict, message: int = None,
                             type_post: str = 'post') -> dict:
        caption = f"""
             <b>{product.name}</b>
             {product.description}
        """

        if type_post == 'post':
            post_data = {
                'media': InputMediaPhoto(
                    open(product.image_path, 'rb'),
                    caption=caption, parse_mode='HTML'
                ),
                'message_id': message
            }
        else:
            post_data = {
                'photo': open(f'{product.image_path}', 'rb'),
                'caption': caption,
                'parse_mode': 'HTML'
            }

        request_forms[f'{type_post}'].append(post_data)
        return request_forms

    async def get_next_page(self, username: str) -> Optional[dict]:
        data = json.loads(await redis_cache.get(username))

        if not (data['current_page'] < len(self.products) - 1):
            return None

        data['current_page'] += 1
        request_forms = {
            'post': [],
            'delete': []
        }

        for message, product in zip_longest(
                data['messages'],
                self.products[data['current_page']],
                fillvalue=None
        ):
            if product is not None:
                request_forms = await self.form_post_data(
                    product=product,
                    request_forms=request_forms,
                    message=message
                )
            else:
                request_forms['delete'].append(message)

        data['messages'] = await self.clear_useless_messages(
            request_forms=request_forms,
            data=data
        )
        request_forms['data'] = data

        return request_forms

    async def get_previous_page(self, username: str) -> Optional[dict]:
        data = json.loads(await redis_cache.get(username))

        if not (data['current_page'] > 0):
            return None

        data['current_page'] -= 1
        request_forms = {
            'post': [],
            'create': []
        }

        for message, product in zip_longest(
                data['messages'],
                self.products[data['current_page']],
                fillvalue=None
        ):
            if message is not None:
                request_forms = await self.form_post_data(
                    product=product,
                    request_forms=request_forms,
                    message=message
                )
            else:
                request_forms = await self.form_post_data(
                    product=product,
                    request_forms=request_forms,
                    type_post='create'
                )

        request_forms['data'] = data
        return request_forms
