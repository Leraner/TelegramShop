from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

callback_data_add_to_basket_or_delete = CallbackData('product_to_basket', 'action', 'product_id')


class InlineKeyboard:
    @staticmethod
    async def generate_switcher_reply_markup(current_page: int, pages: int, callback_data: tuple[str, str]):
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

    @staticmethod
    async def generate_add_to_basket_or_delete_reply_markup(product_id: int, delete_or_add: str):
        markup = InlineKeyboardMarkup()
        if delete_or_add == 'add':
            ib1 = InlineKeyboardButton(
                text='🛒',
                callback_data=callback_data_add_to_basket_or_delete.new(
                    action='add_product_to_basket', product_id=product_id
                ),
            )
        elif delete_or_add == 'delete':
            ib1 = InlineKeyboardButton(
                text='❌',
                callback_data=callback_data_add_to_basket_or_delete.new(
                    action='remove_product_from_basket', product_id=product_id
                ),
            )
        markup.add(ib1)
        return markup
