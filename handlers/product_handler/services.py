import json
from itertools import zip_longest
from typing import Optional

from aiogram.types import InputMediaPhoto

from database.models import Product
from keyboards.inline_keyboard import InlineKeyboard
from loader import redis_cache


class ProductPages:
    @classmethod
    async def _clear_useless_messages(cls, request_forms: dict, data: dict) -> list:
        messages_for_delete = set(request_forms['delete'])
        return [item for item in data['messages'] if item not in messages_for_delete]

    @classmethod
    async def _form_post_data(cls, product: Product, request_forms: dict, reply_markup=None, message: int = None,
                              type_post: str = 'post') -> dict:
        caption = f"""
             <b>{product['name']}</b>
             {product['description']}
        """

        if type_post == 'post':
            post_data = {
                'media': InputMediaPhoto(
                    open(product['image_path'], 'rb'),
                    caption=caption,
                    parse_mode='HTML',
                ),
                'message_id': message,
                'reply_markup': reply_markup
            }
        else:
            post_data = {
                'photo': open(f"{product['image_path']}", 'rb'),
                'caption': caption,
                'parse_mode': 'HTML',
                'reply_markup': reply_markup
            }

        request_forms[f'{type_post}'].append(post_data)
        return request_forms

    @classmethod
    async def get_next_page(cls, username: str, cache_key: str, delete_or_add: str) -> Optional[dict]:
        data = json.loads(await redis_cache.get(username + cache_key))
        products = data['products']

        if not (data['current_page'] < len(products) - 1):
            return None

        data['current_page'] += 1
        request_forms = {
            'post': [],
            'delete': []
        }

        for message, product in zip_longest(
                data['messages'],
                products[data['current_page']],
                fillvalue=None
        ):
            if product is not None:
                request_forms = await cls._form_post_data(
                    product=product,
                    request_forms=request_forms,
                    message=message,
                    reply_markup=await InlineKeyboard.generate_add_to_basket_or_delete_reply_markup(
                        product_id=product['product_id'], delete_or_add=delete_or_add)
                )
            else:
                request_forms['delete'].append(message)

        data['messages'] = await cls._clear_useless_messages(
            request_forms=request_forms,
            data=data
        )
        request_forms['data'] = data

        return request_forms

    @classmethod
    async def get_previous_page(cls, username: str, cache_key: str, delete_or_add: str) -> Optional[dict]:
        data = json.loads(await redis_cache.get(username + cache_key))
        products = data['products']

        if not (data['current_page'] > 0):
            return None

        data['current_page'] -= 1
        request_forms = {
            'post': [],
            'create': []
        }

        for message, product in zip_longest(
                data['messages'],
                products[data['current_page']],
                fillvalue=None
        ):
            if message is not None:
                request_forms = await cls._form_post_data(
                    product=product,
                    request_forms=request_forms,
                    message=message,
                    reply_markup=await InlineKeyboard.generate_add_to_basket_or_delete_reply_markup(
                        product_id=product['product_id'], delete_or_add=delete_or_add)
                )
            else:
                request_forms = await cls._form_post_data(
                    product=product,
                    request_forms=request_forms,
                    type_post='create',
                    reply_markup=await InlineKeyboard.generate_add_to_basket_or_delete_reply_markup(
                        product_id=product['product_id'], delete_or_add=delete_or_add)
                )

        request_forms['data'] = data
        return request_forms
