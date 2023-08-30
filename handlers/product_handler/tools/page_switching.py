from itertools import zip_longest
from typing import Optional

from aiogram.types import InlineKeyboardMarkup, InputMediaPhoto

from database import Product
from keyboards import inline_keyboard


class Pages:
    """ Class for updating current information for redis_cache """

    product_card_create = 'create'
    product_card_delete = 'delete'
    product_card_edit = 'edit'

    @classmethod
    async def _check_previous_page_exists(cls, cache):
        """ Check for the existence of the next page """
        if cache['current_page'] <= 0:
            return False
        return True

    @classmethod
    async def _check_next_page_exists(cls, cache):
        """ Check for the existence of the previous page """
        if cache['current_page'] >= len(cache['products']) - 1:
            return False
        return True

    @classmethod
    async def _clear_useless_messages(cls, request_forms: dict, cache: dict) -> list:
        """ Returns messages in the user's chat at the moment """
        messages_for_delete = set(request_forms[cls.product_card_delete])
        return [item for item in cache['messages'] if item not in messages_for_delete]

    @classmethod
    async def _form_post_data(cls, product: Product, request_forms: dict, reply_markup: InlineKeyboardMarkup = None,
                              message_id: int = None, product_card_type: str = 'edit') -> dict:
        """
        Generate post data and request forms for switching pages
        'edit' - editing existing messages, 'delete' - deleting unwanted messages, 'create' - adding missing messages
        """
        caption = f"""
             <b>{product['name']}</b>
             {product['description']}
        """

        if product_card_type == cls.product_card_edit:
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

        request_forms[f'{product_card_type}'].append(post_data)
        return request_forms

    @classmethod
    async def get_next_page(cls, cache, delete_or_add: str) -> tuple[Optional[dict], dict]:
        """
        Get next page

         cache - cache from redis_cache
         delete_or_add - param which uses for generate buttons on removing or adding product into basket
         :return
         request_forms = {
            'edit': [
                {...}, - product (dict)
            ],
            'delete': [
                int, - message_ids for deleting
            ]
         }
         cache - (dict) - live information of user's products, current page, messages in the chat and e.t.c.
        """
        products = cache['products']
        request_forms = {
            cls.product_card_edit: [],
            cls.product_card_delete: []
        }

        if not await cls._check_next_page_exists(cache):
            return None, cache

        cache['current_page'] += 1

        for message_id, product in zip_longest(cache['messages'], products[cache['current_page']], fillvalue=None):
            if product is not None:
                request_forms = await cls._form_post_data(
                    product=product,
                    request_forms=request_forms,
                    message_id=message_id,
                    reply_markup=await inline_keyboard.generate_add_to_basket_or_delete_reply_markup(
                        product_id=product['product_id'], delete_or_add=delete_or_add)
                )
            else:
                request_forms[cls.product_card_delete].append(message_id)

        cache['messages'] = await cls._clear_useless_messages(
            request_forms=request_forms,
            cache=cache
        )

        return request_forms, cache

    @classmethod
    async def get_previous_page(cls, cache: dict, delete_or_add: str) -> tuple[Optional[dict], dict]:
        """
        Get previous page

         cache - cache from redis_cache
         delete_or_add - param which uses for generate buttons on removing or adding product into basket
         :return
         request_forms = {
            'edit': [
                {...}, - product (dict)
            ],
            'create': [
                int, - message_ids for deleting
            ],
         }
         cache - (dict) - live information of user's products, current page, messages in the chat and e.t.c.
        """
        products = cache['products']
        request_forms = {
            cls.product_card_edit: [],
            cls.product_card_create: []
        }

        if not await cls._check_previous_page_exists(cache):
            return None, cache

        cache['current_page'] -= 1

        for message_id, product in zip_longest(cache['messages'], products[cache['current_page']],
                                               fillvalue=None):
            if message_id is not None:
                request_forms = await cls._form_post_data(
                    product=product,
                    request_forms=request_forms,
                    message_id=message_id,
                    reply_markup=await inline_keyboard.generate_add_to_basket_or_delete_reply_markup(
                        product_id=product['product_id'], delete_or_add=delete_or_add)
                )
            else:
                request_forms = await cls._form_post_data(
                    product=product,
                    request_forms=request_forms,
                    product_card_type=cls.product_card_create,
                    reply_markup=await inline_keyboard.generate_add_to_basket_or_delete_reply_markup(
                        product_id=product['product_id'], delete_or_add=delete_or_add)
                )

        return request_forms, cache
