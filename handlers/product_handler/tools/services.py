from typing import Optional

from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardMarkup

from handlers.product_handler.tools.page_switching import Pages
from keyboards.inline_keyboard import InlineKeyboard


class Service:
    """ Class for sending and editing messages after switching """
    product_object = 'product'
    basket_object = 'basket'

    @classmethod
    async def _generate_cache_frame(cls, all_products: list[list]) -> dict:
        return {
            'messages': [],
            'tab_message': None,
            'current_page': 0,
            'products': all_products
        }

    @classmethod
    async def _check_page_exists(cls, products_next_page: Optional[dict]) -> bool:
        """ Checks for the existence of a previous or next page """
        if products_next_page is None:
            return False
        return True

    @classmethod
    async def _create_messages(cls, dp: Dispatcher, call: types.CallbackQuery, messages: dict, cache: dict) -> dict:
        """ Sends messages to be created after switching to the previous page """
        for form in messages[Pages.product_card_create]:
            new_message = await dp.bot.send_photo(chat_id=call.message.chat.id, **form)
            cache['messages'].append(new_message.message_id)
        return cache

    @classmethod
    async def _send_tab_message(
            cls, message: types.Message, reply_markup_switcher: InlineKeyboardMarkup, json_data: dict) -> dict:
        """ Sends messages with keyboard to switch """
        tab_message = await message.answer('Переключалка', reply_markup=reply_markup_switcher)
        json_data['tab_message'] = tab_message.message_id
        return json_data

    @classmethod
    async def _edit_existing_products(cls, dp: Dispatcher, call: types.CallbackQuery, messages: dict) -> None:
        """ Edits posts after switching page """
        for form in messages[Pages.product_card_edit]:
            await dp.bot.edit_message_media(chat_id=call.message.chat.id, **form)

    @classmethod
    async def _delete_unnecessary_messages(cls, dp: Dispatcher, call: types.CallbackQuery, messages: list) -> None:
        """ Removes posts if there are fewer products on the next page than max_items in pagination """
        for message in messages:
            await dp.bot.delete_message(chat_id=call.message.chat.id, message_id=message)

    @classmethod
    async def _edit_tab_message(cls, call: types.CallbackQuery, current_page: int, pages: int, cache: dict,
                                object: str) -> dict:
        """ Edits the page switching keyboard. Changes the number of the current page """
        tab_message = await call.message.edit_reply_markup(
            await InlineKeyboard.generate_switcher_reply_markup(
                current_page=current_page,
                pages=pages,
                callback_data=(f'{object}_left', f'{object}_right')
            )
        )

        cache['tab_message'] = tab_message.message_id
        return cache

    @classmethod
    async def _create_tab_message(cls, dp: Dispatcher, call: types.CallbackQuery, current_page: int, pages: int,
                                  cache: dict,
                                  object: str) -> dict:
        """ Creates a page switching keyboard after switching to a previous page that has more products """
        tab_message = await dp.bot.send_message(
            chat_id=call.message.chat.id,
            text='Переключалка',
            reply_markup=await InlineKeyboard.generate_switcher_reply_markup(
                current_page=current_page,
                pages=pages,
                callback_data=(f'{object}_left', f'{object}_right')
            )
        )
        cache['tab_message'] = tab_message.message_id
        return cache

    @classmethod
    async def _send_product(cls, message: types.Message, json_data: dict, product: dict,
                            delete_or_add: Optional[str]) -> dict:
        """
        Submits a product with an add or remove cart button.
        In order for the add or delete button to appear, use the delete_or_add parameter
        """
        caption = f"""
             <b>{product['name']}</b>
             {product['description']}
        """

        product_message = await message.answer_photo(
            photo=open(f"{product['image_path']}", 'rb'),
            caption=caption,
            parse_mode='HTML',
            reply_markup=await InlineKeyboard.generate_add_to_basket_or_delete_reply_markup(
                product_id=product['product_id'], delete_or_add=delete_or_add)
        )
        json_data['messages'].append(product_message.message_id)
        return json_data

    @classmethod
    async def show_products(cls, all_products: list[list], message: types.Message,
                            reply_markup_switcher: InlineKeyboardMarkup, delete_or_add: Optional[str] = None) -> dict:
        """Method for displaying products, which is called when products need to be displayed in some handler"""
        json_data = await cls._generate_cache_frame(all_products)

        for product in all_products[0]:
            json_data = await cls._send_product(
                message=message,
                json_data=json_data,
                product=product,
                delete_or_add=delete_or_add
            )

        json_data = await cls._send_tab_message(
            message=message,
            reply_markup_switcher=reply_markup_switcher,
            json_data=json_data
        )
        return json_data

    @classmethod
    async def object_right(cls, dp: Dispatcher, call: types.CallbackQuery, products_next_page: Optional[dict],
                           pages: int,
                           current_page: int,
                           cache: dict, object: str) -> dict:
        """ Right page switch method """
        if not await cls._check_page_exists(products_next_page):
            return cache

        await cls._edit_existing_products(dp=dp, call=call, messages=products_next_page)
        await cls._delete_unnecessary_messages(
            dp=dp, call=call, messages=products_next_page[Pages.product_card_delete])

        cache = await cls._edit_tab_message(
            call=call,
            current_page=current_page + 1,
            pages=pages,
            cache=cache,
            object=object)

        return cache

    @classmethod
    async def object_left(cls, dp: Dispatcher, call: types.CallbackQuery, products_previous_page: dict, pages: int,
                          current_page: int,
                          cache: dict, object: str) -> dict:
        """ Left page switch method """
        if not await cls._check_page_exists(products_previous_page):
            return cache

        if products_previous_page[Pages.product_card_create]:
            await cls._delete_unnecessary_messages(dp=dp, call=call, messages=[cache['tab_message']])

        await cls._edit_existing_products(dp=dp, call=call, messages=products_previous_page)
        cache = await cls._create_messages(dp=dp, call=call, messages=products_previous_page, cache=cache)

        if products_previous_page[Pages.product_card_create]:
            cache = await cls._create_tab_message(
                dp=dp,
                call=call,
                current_page=current_page - 1,
                pages=pages,
                cache=cache,
                object=object)
        else:
            cache = await cls._edit_tab_message(
                call=call,
                current_page=current_page - 1,
                pages=pages,
                cache=cache,
                object=object)
        return cache
