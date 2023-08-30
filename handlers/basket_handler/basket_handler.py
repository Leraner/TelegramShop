from aiogram import types
from sqlalchemy.ext.asyncio import AsyncSession

from actions import product_actions, basket_actions, user_actions
from handlers.product_handler.tools.page_switching import Pages
from handlers.product_handler.tools.services import Service
from keyboards import inline_keyboard, callback_data_add_to_basket_or_delete
from loader import dp

CACHE_KEY = ':basket'


@dp.message_handler(text=inline_keyboard.emoji_commands['basket_command'], content_types=['text'])
async def show_user_basket(message: types.Message, session: AsyncSession) -> None:
    user = await user_actions.get_user_by_username(username=message.from_user.username, session=session)
    user_basket_products = await basket_actions.get_user_basket(user_id=user.user_id, session=session)

    if len(user_basket_products) == 0:
        await message.answer('Ваша корзина пуста')
        return

    markup_switcher = await inline_keyboard.generate_switcher_reply_markup(
        current_page=1,
        pages=len(user_basket_products),
        callback_data=('basket_left', 'basket_right')
    )

    json_data = await Service.show_products(
        all_products=user_basket_products, message=message, reply_markup_switcher=markup_switcher,
        delete_or_add=inline_keyboard.delete_from_basket
    )

    await dp.bot.set_cache(username=message.from_user.username, cache_key=CACHE_KEY, cache=json_data)


@dp.callback_query_handler(callback_data_add_to_basket_or_delete.filter(action='remove_product_from_basket'))
async def remove_product_from_basket(call: types.CallbackQuery, callback_data: dict, session: AsyncSession) -> None:
    user = await user_actions.get_user_by_username(username=call.from_user.username, session=session)
    product = await product_actions.get_product_by_id(product_id=int(callback_data['product_id']), session=session)
    if not (product in user.basket.products):
        await call.answer(text='🥵Такого товара уже нет в вашей корзине', show_alert=True)
    else:
        new_user = await basket_actions.remove_product_from_basket(user=user, product=product, session=session)
        await call.answer(text='✅Товар удален из корзины', show_alert=True)


@dp.callback_query_handler(text=['basket_left'])
async def basket_left(call: types.CallbackQuery) -> None:
    """ Handler for switching the cart page to the right """
    current_page, pages = call.message.reply_markup.inline_keyboard[0][1].text.split('/')
    products_previous_page, cache = await Pages.get_previous_page(
        cache=await dp.bot.get_cache(username=call.from_user.username, cache_key=CACHE_KEY),
        delete_or_add=inline_keyboard.delete_from_basket
    )

    cache = await Service.object_left(
        dp=dp,
        call=call,
        products_previous_page=products_previous_page,
        pages=int(pages),
        current_page=int(current_page),
        cache=cache,
        object=Service.basket_object
    )
    await dp.bot.set_cache(username=call.from_user.username, cache_key=CACHE_KEY, cache=cache)


@dp.callback_query_handler(text=['basket_right'])
async def basket_right(call: types.CallbackQuery) -> None:
    """ Handler for switching the cart page to the left """
    current_page, pages = call.message.reply_markup.inline_keyboard[0][1].text.split('/')
    products_next_page, cache = await Pages.get_next_page(
        cache=await dp.bot.get_cache(username=call.from_user.username, cache_key=CACHE_KEY),
        delete_or_add=inline_keyboard.delete_from_basket
    )

    cache = await Service.object_right(
        dp=dp,
        call=call,
        products_next_page=products_next_page,
        pages=int(pages),
        current_page=int(current_page),
        cache=cache,
        object=Service.basket_object
    )

    await dp.bot.set_cache(username=call.from_user.username, cache_key=CACHE_KEY, cache=cache)
