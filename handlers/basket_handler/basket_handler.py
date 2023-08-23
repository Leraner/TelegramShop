import json

from aiogram import types
from sqlalchemy.ext.asyncio import AsyncSession

from actions.basket_actions.basket_actions import BasketActions
from actions.user_actions.user_actions import UserActions
from handlers.product_handler.services import Pages
from keyboards.inline_keyboard import InlineKeyboard, callback_data_add_to_basket_or_delete
from loader import dp, basket_actions, redis_cache, product_actions

CACHE_KEY = ':basket'


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

    if len(user_basket_products) == 0:
        msg = await message.answer('Ваша корзина пуста')
        useless_messages = json.loads(await redis_cache.get(message.from_user.username + ':useless_messages'))
        useless_messages.append(msg.message_id)
        await redis_cache.set(message.from_user.username + ':useless_messages', json.dumps(useless_messages))
        return

    for product in user_basket_products[0]:
        caption = f"""
             <b>{product['name']}</b>
             {product['description']}
        """
        product_message = await message.answer_photo(
            open(f"{product['image_path']}", 'rb'),
            caption=caption,
            parse_mode='HTML',
            reply_markup=await InlineKeyboard.generate_add_to_basket_or_delete_reply_markup(
                product_id=product['product_id'], delete_or_add='delete'
            )
        )
        json_data['messages'].append(product_message.message_id)

    tab_message = await message.answer(
        'Переключалка',
        reply_markup=await InlineKeyboard.generate_switcher_reply_markup(
            current_page=1,
            pages=len(user_basket_products),
            callback_data=('basket_left', 'basket_right')
        )
    )
    json_data['tab_message'] = tab_message.message_id

    await redis_cache.set(
        message.from_user.username + CACHE_KEY,
        json.dumps(json_data, default=str)
    )


@dp.callback_query_handler(callback_data_add_to_basket_or_delete.filter(action='remove_product_from_basket'))
async def remove_product_from_basket(call: types.CallbackQuery, callback_data: dict, session: AsyncSession) -> None:
    user = await UserActions.get_user_by_username(username=call.from_user.username, session=session)
    product = await product_actions.get_product_by_id(product_id=int(callback_data['product_id']), session=session)
    if not (product in user.basket.products):
        await call.answer(text='🥵Такого товара уже нет в вашей корзине', show_alert=True)
    else:
        new_user = await BasketActions.remove_product_from_basket(user=user, product=product, session=session)
        await call.answer(text='✅Товар удален из корзины', show_alert=True)


@dp.callback_query_handler(text=['basket_left'])
async def basket_left(call: types.CallbackQuery) -> None:
    current_page, pages = call.message.reply_markup.inline_keyboard[0][1].text.split('/')
    products_previous_page = await Pages.get_previous_page(
        username=call.from_user.username,
        cache_key=CACHE_KEY,
        delete_or_add='delete'
    )

    if products_previous_page is None:
        return

    cache = products_previous_page['cache']

    if len(products_previous_page['create']) > 0:
        await dp.bot.delete_message(
            chat_id=call.message.chat.id, message_id=cache['tab_message']
        )

    for form in products_previous_page['post']:
        await dp.bot.edit_message_media(chat_id=call.message.chat.id, **form)

    for form in products_previous_page['create']:
        new_message = await dp.bot.send_photo(chat_id=call.message.chat.id, **form)
        cache['messages'].append(new_message.message_id)

    if len(products_previous_page['create']) > 0:
        tab_message = await dp.bot.send_message(
            chat_id=call.message.chat.id,
            text='Переключалка',
            reply_markup=await InlineKeyboard.generate_switcher_reply_markup(
                int(current_page) - 1, pages, callback_data=('basket_left', 'basket_right')
            )
        )
    else:
        tab_message = await call.message.edit_reply_markup(
            await InlineKeyboard.generate_switcher_reply_markup(
                int(current_page) - 1, pages, callback_data=('basket_left', 'basket_right')
            )
        )

    cache['tab_message'] = tab_message.message_id
    await redis_cache.set(call.from_user.username + CACHE_KEY, json.dumps(cache))


@dp.callback_query_handler(text=['basket_right'])
async def basket_right(call: types.CallbackQuery) -> None:
    current_page, pages = call.message.reply_markup.inline_keyboard[0][1].text.split('/')
    products_next_page = await Pages.get_next_page(
        username=call.from_user.username,
        cache_key=CACHE_KEY,
        delete_or_add='delete'
    )

    if products_next_page is None:
        return

    cache = products_next_page['cache']

    for form in products_next_page['post']:
        await dp.bot.edit_message_media(chat_id=call.message.chat.id, **form)

    for message in products_next_page['delete']:
        await dp.bot.delete_message(chat_id=call.message.chat.id, message_id=message)

    tab_message = await call.message.edit_reply_markup(
        await InlineKeyboard.generate_switcher_reply_markup(
            int(current_page) + 1, pages, callback_data=('basket_left', 'basket_right')
        )
    )

    cache['tab_message'] = tab_message.message_id
    await redis_cache.set(call.from_user.username + CACHE_KEY, json.dumps(cache))
