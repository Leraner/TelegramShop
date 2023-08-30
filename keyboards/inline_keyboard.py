from typing import Optional

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.callback_data import CallbackData
from sqlalchemy.ext.asyncio import AsyncSession

from actions import category_actions

callback_data_add_to_basket_or_delete = CallbackData('product_to_basket', 'action', 'product_id')
callback_data_select_category_for_product = CallbackData('category_for_product', 'action', 'category_id')


class InlineKeyboard:
    """Class inlinekeboard generator"""

    def __init__(self):
        self.delete_from_basket = 'delete'
        self.add_to_basket = 'add'

        self.emoji_commands = {
            'find_command': '🔎',
            'basket_command': '🗑',
            'all_products_command': '🗃',
            'create_product_command': '🗳'
        }

        self.emoji = [self.emoji_commands[command] for command in self.emoji_commands]

    @staticmethod
    async def generate_switcher_reply_markup(current_page: int, pages: int,
                                             callback_data: tuple[str, str]) -> InlineKeyboardMarkup:
        """Generates a keyboard that switches pages"""
        markup = InlineKeyboardMarkup()
        ib1 = InlineKeyboardButton(
            text='<',
            callback_data=f'{callback_data[0]}'
        )
        ib2 = InlineKeyboardButton(
            text=f'{current_page}/{pages}',
            callback_data='1/1'
        )
        ib3 = InlineKeyboardButton(
            text='>',
            callback_data=f'{callback_data[1]}'
        )
        markup.add(ib1, ib2, ib3)
        return markup

    async def generate_add_to_basket_or_delete_reply_markup(self, product_id: int,
                                                            delete_or_add: str = None) -> Optional[InlineKeyboardMarkup]:
        """
        Generates buttons for removing and adding products to basket

        product_id - id of product which will add or remove from basket
        delete_or_add - param which say what buttons to create (for adding or for removing)
        """
        markup = InlineKeyboardMarkup()
        if delete_or_add == self.add_to_basket:
            ib1 = InlineKeyboardButton(
                text='🛒',
                callback_data=callback_data_add_to_basket_or_delete.new(
                    action='add_product_to_basket', product_id=product_id
                ),
            )
        elif delete_or_add == self.delete_from_basket:
            ib1 = InlineKeyboardButton(
                text='❌',
                callback_data=callback_data_add_to_basket_or_delete.new(
                    action='remove_product_from_basket', product_id=product_id
                ),
            )
        else:
            return None
        markup.add(ib1)
        return markup

    async def generate_commands_reply_keyboard_markup(self, user_is_admin: bool = False) -> ReplyKeyboardMarkup:
        """
        Generate buttons that helps the user send commands
        user_is_admin - if true, add additional buttons
        """
        markup = ReplyKeyboardMarkup()
        btn1 = KeyboardButton(text=self.emoji_commands['basket_command'])
        btn2 = KeyboardButton(text=self.emoji_commands['all_products_command'])
        btn4 = KeyboardButton(text=self.emoji_commands['find_command'])
        if user_is_admin:
            btn3 = KeyboardButton(text=self.emoji_commands['create_product_command'])
            markup.add(btn3)
        markup.add(btn1, btn2, btn4)
        return markup

    @staticmethod
    async def generate_category_reply_markup(session: AsyncSession) -> InlineKeyboardMarkup:
        """Generate buttons for send all categories"""
        markup = InlineKeyboardMarkup(row_width=1)
        categories = await category_actions.get_all_categories(session=session)
        for category in categories:
            markup.insert(
                InlineKeyboardButton(
                    text=f'{category["name"]}',
                    callback_data=callback_data_select_category_for_product.new(
                        action='select_category',
                        category_id=category['category_id']
                    )
                )
            )
        return markup
