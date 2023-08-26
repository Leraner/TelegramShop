import datetime
import json

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ContentType
from sqlalchemy.ext.asyncio import AsyncSession

from actions import product_actions, basket_actions, user_actions
from exceptions.exceptions import PermissionDenied, SerializerValidationError
from handlers.product_handler.services import Pages, Service
from keyboards.inline_keyboard import InlineKeyboard, callback_data_add_to_basket_or_delete, \
    callback_data_select_category_for_product
from loader import dp, redis_cache, elastic_search_client
from state.states import ProductState, SearchProductState

CACHE_KEY = ':product'


@dp.message_handler(commands=['find'])
async def search_products(message: types.Message, session: AsyncSession, state: FSMContext) -> None:
    msg = await message.answer('Введите, что вы хотите найти')
    await Service.set_unused_messages_into_cache(
        [msg.message_id], message.from_user.username + ':useless_messages'
    )
    await state.set_state(SearchProductState.SEARCH_REQUEST)


@dp.message_handler(state=SearchProductState.SEARCH_REQUEST)
async def search_products(message: types.Message, session: AsyncSession, state: FSMContext) -> None:
    search_request = message.text
    searching_result = await elastic_search_client.search_elastic_products(search_request)
    await Service.set_unused_messages_into_cache(
        [message.message_id], message.from_user.username + ':useless_messages'
    )

    if len(searching_result) == 0:
        msg = await message.answer('По вашему запросу ничего не найдено')
        await Service.set_unused_messages_into_cache(
            [msg.message_id], message.from_user.username + ':useless_messages'
        )
        await state.finish()
        return

    json_data = await Service.show_products(all_products=searching_result, message=message)

    await redis_cache.set(
        message.from_user.username + CACHE_KEY,
        json.dumps(json_data, default=str)
    )
    await state.finish()


@dp.message_handler(commands=['create_product'])
async def create_product(message: types.Message, session: AsyncSession, state: FSMContext) -> None:
    msg = await message.answer('Напишите название продукта')
    await Service.set_unused_messages_into_cache([msg.message_id], message.from_user.username + ':useless_messages')
    await state.set_state(ProductState.START_CREATION)


@dp.message_handler(state=ProductState.START_CREATION)
async def create_product_category(message: types.Message, session: AsyncSession, state: FSMContext) -> None:
    product_name = message.text
    await state.update_data(NAME=product_name)
    msg = await message.answer(
        'Выберите категорию для продукта',
        reply_markup=await InlineKeyboard.generate_category_reply_markup(session=session)
    )
    await Service.set_unused_messages_into_cache(
        [message.message_id, msg.message_id],
        message.from_user.username + ':useless_messages'
    )
    await state.set_state(ProductState.CATEGORY)


@dp.callback_query_handler(
    callback_data_select_category_for_product.filter(action='select_category'),
    state=ProductState.CATEGORY
)
async def create_product_get_name(call: types.CallbackQuery, callback_data: dict, session: AsyncSession,
                                  state: FSMContext) -> None:
    await state.update_data(CATEGORY=int(callback_data['category_id']))
    msg = await call.message.answer('Напишите описание к продукту')
    await Service.set_unused_messages_into_cache([msg.message_id], call.from_user.username + ':useless_messages')
    await state.set_state(ProductState.DESCRIPTION)


@dp.message_handler(state=ProductState.DESCRIPTION)
async def create_product_get_image(message: types.Message, session: AsyncSession, state: FSMContext) -> None:
    product_description = message.text
    await state.update_data(DESCRIPTION=product_description)
    msg = await message.answer('Пришлите изображение продукта')
    await Service.set_unused_messages_into_cache(
        [msg.message_id, message.message_id],
        message.from_user.username + ':useless_messages'
    )
    await state.set_state(ProductState.IMAGE_PATH)


@dp.message_handler(state=ProductState.IMAGE_PATH, content_types=ContentType.PHOTO)
async def create_product_get_image(message: types.Message, session: AsyncSession, state: FSMContext) -> None:
    photo = message.photo[1]
    date = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    date_file_name = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    path = f'media/products_images/{date}/{date_file_name}.png'
    await photo.download(destination_file=path)

    product_state_data = await state.get_data()
    data = {
        'name': product_state_data['NAME'],
        'description': product_state_data['DESCRIPTION'],
        'image_path': path,
        'category_id': product_state_data['CATEGORY']
    }
    try:
        new_product = await product_actions.create_product(
            data=data,
            session=session,
            user=await user_actions.get_user_by_username(message.from_user.username, session=session),
        )
    except (PermissionDenied, SerializerValidationError) as error:
        msg = await message.answer(error.message)
        await Service.set_unused_messages_into_cache(
            [msg.message_id, message.message_id],
            message.from_user.username + ':useless_messages'
        )
    else:
        msg1 = await message.answer('Продукт успешно создан')
        caption = f"""
            <b>{new_product.name}</b>
            {new_product.description}
        """
        msg2 = await message.answer_photo(
            open(f'{new_product.image_path}', 'rb'),
            caption=caption,
            parse_mode='HTML'
        )
        await Service.set_unused_messages_into_cache(
            [msg1.message_id, msg2.message_id, message.message_id],
            message.from_user.username + ':useless_messages'
        )
    await state.finish()


@dp.callback_query_handler(callback_data_add_to_basket_or_delete.filter(action='add_product_to_basket'))
async def add_product_to_basket(call: types.CallbackQuery, callback_data: dict, session: AsyncSession) -> None:
    user = await user_actions.get_user_by_username(username=call.from_user.username, session=session)
    product = await product_actions.get_product_by_id(product_id=int(callback_data['product_id']), session=session)
    if product in user.basket.products:
        await call.answer(text='🥵Товар уже есть в корзине', show_alert=True)
    else:
        new_user = await basket_actions.add_product_to_user_basket(user=user, product=product, session=session)
        await call.answer(text='✅Товар добавлен в корзину', show_alert=True)


@dp.message_handler(commands=['show_products'])
async def show_all_products(message: types.Message, session: AsyncSession) -> None:
    all_products = await product_actions.get_all_products(session=session)

    if len(all_products) == 0:
        msg = await message.answer('Продукты скоро появятся')
        await Service.set_unused_messages_into_cache(
            [msg.message_id], message.from_user.username + ':useless_messages'
        )
        return

    json_data = await Service.show_products(all_products=all_products, message=message)

    await redis_cache.set(
        message.from_user.username + CACHE_KEY,
        json.dumps(json_data, default=str)
    )


@dp.callback_query_handler(text=['product_left'])
async def product_left(call: types.CallbackQuery) -> None:
    """Switch to the previous page"""
    current_page, pages = call.message.reply_markup.inline_keyboard[0][1].text.split('/')
    products_previous_page = await Pages.get_previous_page(
        username=call.from_user.username,
        cache_key=CACHE_KEY,
        delete_or_add='add'
    )

    if products_previous_page is None:
        return

    cache = products_previous_page.pop('cache')

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
                current_page=int(current_page) - 1,
                pages=pages,
                callback_data=('product_left', 'product_right')
            )
        )
    else:
        tab_message = await call.message.edit_reply_markup(
            await InlineKeyboard.generate_switcher_reply_markup(
                current_page=int(current_page) - 1,
                pages=pages,
                callback_data=('product_left', 'product_right')
            )
        )

    cache['tab_message'] = tab_message.message_id
    await redis_cache.set(call.from_user.username + CACHE_KEY, json.dumps(cache))


@dp.callback_query_handler(text=['product_right'])
async def product_right(call: types.CallbackQuery) -> None:
    """Switch to the next page"""
    current_page, pages = call.message.reply_markup.inline_keyboard[0][1].text.split('/')
    products_next_page = await Pages.get_next_page(
        username=call.from_user.username,
        cache_key=CACHE_KEY,
        delete_or_add='add'
    )

    if products_next_page is None:
        return

    cache = products_next_page.pop('cache')

    for form in products_next_page['post']:
        await dp.bot.edit_message_media(chat_id=call.message.chat.id, **form)

    for message in products_next_page['delete']:
        await dp.bot.delete_message(chat_id=call.message.chat.id, message_id=message)

    tab_message = await call.message.edit_reply_markup(
        await InlineKeyboard.generate_switcher_reply_markup(
            current_page=int(current_page) + 1,
            pages=pages,
            callback_data=('product_left', 'product_right')
        )
    )

    cache['tab_message'] = tab_message.message_id
    await redis_cache.set(call.from_user.username + CACHE_KEY, json.dumps(cache))
