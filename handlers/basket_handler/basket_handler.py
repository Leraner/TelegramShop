import json

from aiogram import types
from sqlalchemy.ext.asyncio import AsyncSession

from actions.user_actions.user_actions import UserActions
from handlers.product_handler.services import ProductPages
from keyboards.inline_keyboard import InlineKeyboard
from loader import dp, basket_actions, redis_cache

CACHE_KEY = ':basket'


# @dp.message_handler(commands=['test'])
# async def test(message: types.Message, session: AsyncSession) -> None:
#     user = await UserActions.get_user_by_username(username=message.from_user.username, session=session)
#     product = await product_actions.get_product_by_id(product_id=6, session=session)
#     new_user = await BasketActions.add_product_to_user_basket(user=user, product=product, session=session)


@dp.message_handler(commands=['basket'])
async def show_user_basket(message: types.Message, session: AsyncSession) -> None:
    user = await UserActions.get_user_by_username(username=message.from_user.username, session=session)
    user_basket_products = await basket_actions.get_user_basket(user_id=user.user_id, session=session)

    json_data = {
        'messages': [],
        'tab_message': None,
        'current_page': 0,
        'products': user_basket_products
    }

    if user_basket_products is None:
        await message.answer('Ваша корзина пуста')
        return

    for product in user_basket_products[0]:
        caption = f"""
             <b>{product['name']}</b>
             {product['description']}
        """
        product_message = await message.answer_photo(
            open(f"{product['image_path']}", 'rb'),
            caption=caption,
            parse_mode='HTML'
        )
        json_data['messages'].append(product_message.message_id)

    tab_message = await message.answer(
        'Переключалка',
        reply_markup=await InlineKeyboard.generate_keyboard(1, len(user_basket_products))
    )
    json_data['tab_message'] = tab_message.message_id

    await redis_cache.set(message.from_user.username + CACHE_KEY, json.dumps(json_data, default=str))


@dp.callback_query_handler(text=['<'])
async def left(call: types.CallbackQuery) -> None:
    current_page, pages = call.message.reply_markup.inline_keyboard[0][1].text.split('/')
    products_previous_page = await ProductPages.get_previous_page(username=call.from_user.username,
                                                                  cache_key=CACHE_KEY)

    if products_previous_page is None:
        return

    data = products_previous_page['data']

    if len(products_previous_page['create']) > 0:
        await dp.bot.delete_message(chat_id=call.message.chat.id, message_id=data['tab_message'])

    for form in products_previous_page['post']:
        await dp.bot.edit_message_media(chat_id=call.message.chat.id, **form)
    for form in products_previous_page['create']:
        new_message = await dp.bot.send_photo(chat_id=call.message.chat.id, **form)
        data['messages'].append(new_message.message_id)

    if len(products_previous_page['create']) > 0:
        tab_message = await dp.bot.send_message(
            chat_id=call.message.chat.id,
            text='Переключалка',
            reply_markup=await InlineKeyboard.generate_keyboard(int(current_page) - 1, pages)
        )
    else:
        tab_message = await call.message.edit_reply_markup(
            await InlineKeyboard.generate_keyboard(int(current_page) - 1, pages)
        )

    data['tab_message'] = tab_message.message_id
    await redis_cache.set(call.from_user.username + CACHE_KEY, json.dumps(data))


@dp.callback_query_handler(text=['>'])
async def right(call: types.CallbackQuery) -> None:
    current_page, pages = call.message.reply_markup.inline_keyboard[0][1].text.split('/')
    products_next_page = await ProductPages.get_next_page(username=call.from_user.username,
                                                          cache_key=CACHE_KEY)

    if products_next_page is None:
        return

    for form in products_next_page['post']:
        await dp.bot.edit_message_media(chat_id=call.message.chat.id, **form)
    for message in products_next_page['delete']:
        await dp.bot.delete_message(chat_id=call.message.chat.id, message_id=message)

    tab_message = await call.message.edit_reply_markup(
        await InlineKeyboard.generate_keyboard(int(current_page) + 1, pages)
    )

    data = products_next_page['data']
    data['tab_message'] = tab_message.message_id
    await redis_cache.set(call.from_user.username + CACHE_KEY, json.dumps(data))
