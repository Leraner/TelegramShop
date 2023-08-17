from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class InlineKeyboard:
    @staticmethod
    async def generate_keyboard(current_page: int, pages: int):
        markup = InlineKeyboardMarkup()
        ib1 = InlineKeyboardButton(
            text='<',
            callback_data='<'
        )
        ib2 = InlineKeyboardButton(
            text=f'{current_page}/{pages}',
            callback_data='1/1'
        )
        ib3 = InlineKeyboardButton(
            text='>',
            callback_data='>'
        )
        markup.add(ib1, ib2, ib3)
        return markup
