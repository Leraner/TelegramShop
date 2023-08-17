from itertools import zip_longest
from typing import Optional

from aiogram.types import InputMediaPhoto


class ProductPages:
    def __init__(self, products: list = None, messages: list = [], tab_message_id: int = None):
        self.products = products
        self.current_page = 0
        self.messages = messages
        self.tab_message_id = tab_message_id

    def get_current_page(self) -> list:
        return self.products[self.current_page]

    def get_next_page(self) -> Optional[dict]:
        if self.current_page < len(self.products) - 1:
            self.current_page += 1
            request_forms = {'post': [], 'delete': []}
            for message, product in zip_longest(self.messages, self.products[self.current_page], fillvalue=None):
                if product is not None:
                    caption = f"""
                         <b>{product.name}</b>
                         {product.description}
                     """
                    request_forms['post'].append({
                        'media': InputMediaPhoto(
                            open(product.image_path, 'rb'),
                            caption=caption, parse_mode='HTML'
                        ),
                        'message_id': message
                    })
                else:
                    request_forms['delete'].append(message)
            messages_for_delete = set(request_forms['delete'])
            self.messages = [item for item in self.messages if item not in messages_for_delete]
            return request_forms
        return None

    def get_previous_page(self) -> Optional[dict]:
        if self.current_page > 0:
            self.current_page -= 1
            request_forms = {'post': [], 'create': []}
            for message, product in zip_longest(self.messages, self.products[self.current_page], fillvalue=None):
                caption = f"""
                     <b>{product.name}</b>
                     {product.description}
                 """
                if message is not None:
                    request_forms['post'].append({
                        'media': InputMediaPhoto(
                            open(product.image_path, 'rb'),
                            caption=caption, parse_mode='HTML'
                        ),
                        'message_id': message
                    })
                else:
                    request_forms['create'].append({
                        'photo': open(f'{product.image_path}', 'rb'),
                        'caption': caption,
                        'parse_mode': 'HTML'
                    })
            return request_forms
        return None
