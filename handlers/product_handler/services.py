import json
from itertools import zip_longest
from typing import Optional

from aiogram import types
from aiogram.types import InputMediaPhoto, InlineKeyboardMarkup

from database.models import Product
from keyboards.inline_keyboard import InlineKeyboard
from loader import redis_cache


class Service:
    @staticmethod
    async def set_unused_messages_into_cache(message: list, key: str) -> None:
        """
        Method that sends messages to redis cache with ':useless_messages' key.
        So that later messages are deleted when another command is called
        """
        useless_messages = json.loads(await redis_cache.get(key))
        useless_messages.extend(message)
        await redis_cache.set(key, json.dumps(useless_messages))

    @staticmethod
    async def show_products(all_products: list[list], message: types.Message) -> dict:
        """Method for displaying products, which is called when products need to be displayed in some handler"""
        json_data = {
            'messages': [],
            'tab_message': None,
            'current_page': 0,
            'products': all_products
        }

        for product in all_products[0]:
            caption = f"""
                     <b>{product['name']}</b>
                     {product['description']}
                """
            product_message = await message.answer_photo(
                open(f"{product['image_path']}", 'rb'),
                caption=caption,
                parse_mode='HTML',
                reply_markup=await InlineKeyboard.generate_add_to_basket_or_delete_reply_markup(
                    product_id=product['product_id'], delete_or_add='add'
                )
            )
            json_data['messages'].append(product_message.message_id)

        tab_message = await message.answer(
            'Переключалка',
            reply_markup=await InlineKeyboard.generate_switcher_reply_markup(
                current_page=1,
                pages=len(all_products),
                callback_data=('product_left', 'product_right')
            )
        )
        json_data['tab_message'] = tab_message.message_id

        return json_data


class Pages:
    """Class for switching pages"""

    @classmethod
    async def _clear_useless_messages(cls, request_forms: dict, cache: dict) -> list:
        """
        Clear unused messages in the live user's information which will send in redis cache
        """
        messages_for_delete = set(request_forms['delete'])
        return [item for item in cache['messages'] if item not in messages_for_delete]

    @classmethod
    async def _form_post_data(cls, product: Product, request_forms: dict, reply_markup: InlineKeyboardMarkup = None,
                              message_id: int = None, type_post: str = 'post') -> dict:
        """
        Generate post data and request forms for switching pages

        product - (Product) - product
        request_forms - (dict) - {'post': ..., 'delete/create': ...},
        'post' - editing existing messages, 'delete' - deleting unwanted messages, 'create' - adding missing messages
        reply_markup - (InlineKeyboardMarkup, default=None) - buttons for adding or removing from basket
        message_id - (int, default None) - message_id
        type_post - (string, default 'post') - param which says editing or create new message with product
        """
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
                'message_id': message_id,
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
        """
        Get next page

         username - (string) - user username
         cache_key - (string) - key which uses for adding pages information into redis cache
         delete_or_add - (string) - param which uses for generate buttons on removing or adding product into basket
         :return
         request_forms = {
            'post': [
                {...}, - product
            ],
            'delete': [
                int, - message_ids for deleting
            ],
            'cache': dict - live information of user's products, current page, messages in the chat and e.t.c.
         }
        """
        cache = json.loads(await redis_cache.get(username + cache_key))
        products = cache['products']

        if not (cache['current_page'] < len(products) - 1):
            return None

        cache['current_page'] += 1
        request_forms = {
            'post': [],
            'delete': []
        }

        for message_id, product in zip_longest(
                cache['messages'],
                products[cache['current_page']],
                fillvalue=None
        ):
            if product is not None:
                request_forms = await cls._form_post_data(
                    product=product,
                    request_forms=request_forms,
                    message_id=message_id,
                    reply_markup=await InlineKeyboard.generate_add_to_basket_or_delete_reply_markup(
                        product_id=product['product_id'], delete_or_add=delete_or_add)
                )
            else:
                request_forms['delete'].append(message_id)

        cache['messages'] = await cls._clear_useless_messages(
            request_forms=request_forms,
            cache=cache
        )
        request_forms['cache'] = cache

        return request_forms

    @classmethod
    async def get_previous_page(cls, username: str, cache_key: str, delete_or_add: str) -> Optional[dict]:
        """
        Get previous page

         username - (string) - user username
         cache_key - (string) - key which uses for adding pages information into redis cache
         delete_or_add - (string) - param which uses for generate buttons on removing or adding product into basket
         :return
         request_forms = {
            'post': [
                {...}, - product
            ],
            'delete': [
                int, - message_ids for deleting
            ],
            'cache': dict - live information of user's products, current page, messages in the chat and e.t.c.
         }
        """
        cache = json.loads(await redis_cache.get(username + cache_key))
        products = cache['products']

        if not (cache['current_page'] > 0):
            return None

        cache['current_page'] -= 1
        request_forms = {
            'post': [],
            'create': []
        }

        for message_id, product in zip_longest(
                cache['messages'],
                products[cache['current_page']],
                fillvalue=None
        ):
            if message_id is not None:
                request_forms = await cls._form_post_data(
                    product=product,
                    request_forms=request_forms,
                    message_id=message_id,
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

        request_forms['cache'] = cache
        return request_forms
