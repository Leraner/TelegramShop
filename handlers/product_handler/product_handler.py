import datetime
import logging

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ContentType
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from actions import product_actions, basket_actions, user_actions
from exceptions.exceptions import PermissionDenied, SerializerValidationError
from handlers.product_handler.tools.page_switching import Pages
from handlers.product_handler.tools.services import Service
from keyboards.inline_keyboard import InlineKeyboard, callback_data_add_to_basket_or_delete, \
    callback_data_select_category_for_product
from loader import dp, elastic_search_client
from state.states import ProductState, SearchProductState

CACHE_KEY = ':product'


@dp.message_handler(commands=['find'])
async def search_products(message: types.Message, session: AsyncSession, state: FSMContext) -> None:
    await message.answer('Введите, что вы хотите найти')
    await state.set_state(SearchProductState.SEARCH_REQUEST)


@dp.message_handler(state=SearchProductState.SEARCH_REQUEST)
async def search_products(message: types.Message, session: AsyncSession, state: FSMContext) -> None:
    search_request = message.text
    searching_result = await elastic_search_client.search_elastic_products(search_request)

    if len(searching_result) == 0:
        await message.answer('По вашему запросу ничего не найдено')
        await state.finish()
        return

    markup_switcher = await InlineKeyboard.generate_switcher_reply_markup(
        current_page=1,
        pages=len(searching_result),
        callback_data=('product_left', 'product_right')
    )

    json_data = await Service.show_products(
        all_products=searching_result,
        message=message,
        reply_markup_switcher=markup_switcher,
        delete_or_add=InlineKeyboard.add_to_basket)

    await dp.bot.set_cache(username=message.from_user.username, cache_key=CACHE_KEY, cache=json_data)
    await state.finish()


@dp.message_handler(commands=['create_product'])
async def create_product(message: types.Message, session: AsyncSession, state: FSMContext) -> None:
    await message.answer('Напишите название продукта')
    await state.set_state(ProductState.START_CREATION)


@dp.message_handler(state=ProductState.START_CREATION)
async def create_product_category(message: types.Message, session: AsyncSession, state: FSMContext) -> None:
    product_name = message.text
    await state.update_data(NAME=product_name)
    await message.answer(
        'Выберите категорию для продукта',
        reply_markup=await InlineKeyboard.generate_category_reply_markup(session=session)
    )
    await state.set_state(ProductState.CATEGORY)


@dp.callback_query_handler(
    callback_data_select_category_for_product.filter(action='select_category'),
    state=ProductState.CATEGORY
)
async def create_product_get_name(call: types.CallbackQuery, callback_data: dict, session: AsyncSession,
                                  state: FSMContext) -> None:
    await state.update_data(CATEGORY=int(callback_data['category_id']))
    await call.message.answer('Напишите описание к продукту')
    await state.set_state(ProductState.DESCRIPTION)


@dp.message_handler(state=ProductState.DESCRIPTION)
async def create_product_get_image(message: types.Message, session: AsyncSession, state: FSMContext) -> None:
    product_description = message.text
    await state.update_data(DESCRIPTION=product_description)
    await message.answer('Пришлите изображение продукта')
    await state.set_state(ProductState.IMAGE_PATH)


@dp.message_handler(state=ProductState.IMAGE_PATH, content_types=ContentType.PHOTO)
async def create_product_get_image(message: types.Message, session: AsyncSession, state: FSMContext) -> None:
    photo = message.photo[1]
    date = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    date_file_name = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    path = f'media/products_images/{date}/{date_file_name}.png'

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
        await photo.download(destination_file=path)
    except (PermissionDenied, SerializerValidationError, ValidationError) as error:
        await message.answer(error.message)
    else:
        await message.answer('Продукт успешно создан')
        caption = f"""
            <b>{new_product.name}</b>
            {new_product.description}
        """
        await message.answer_photo(
            open(f'{new_product.image_path}', 'rb'),
            caption=caption,
            parse_mode='HTML'
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
        await message.answer('Продукты скоро появятся')
        return

    markup_switcher = await InlineKeyboard.generate_switcher_reply_markup(
        current_page=1,
        pages=len(all_products),
        callback_data=('product_left', 'product_right')
    )

    json_data = await Service.show_products(
        all_products=all_products,
        message=message,
        reply_markup_switcher=markup_switcher,
        delete_or_add=InlineKeyboard.add_to_basket
    )

    await dp.bot.set_cache(username=message.from_user.username, cache_key=CACHE_KEY, cache=json_data)


@dp.callback_query_handler(text=['product_left'])
async def product_left(call: types.CallbackQuery) -> None:
    """ Handler to switch the page of all products to the left """
    current_page, pages = call.message.reply_markup.inline_keyboard[0][1].text.split('/')
    products_previous_page, cache = await Pages.get_previous_page(
        cache=await dp.bot.get_cache(username=call.from_user.username, cache_key=CACHE_KEY),
        delete_or_add=InlineKeyboard.add_to_basket
    )

    cache = await Service.object_left(
        dp=dp,
        call=call,
        products_previous_page=products_previous_page,
        pages=int(pages),
        current_page=int(current_page),
        cache=cache,
        object=Service.product_object
    )

    logging.info(f'SWITCHED PREVIOUS PAGE INTO {call.from_user.username} CHAT')

    await dp.bot.set_cache(username=call.from_user.username, cache_key=CACHE_KEY, cache=cache)


@dp.callback_query_handler(text=['product_right'])
async def product_right(call: types.CallbackQuery) -> None:
    """ Handler to switch the page of all products to the right """
    current_page, pages = call.message.reply_markup.inline_keyboard[0][1].text.split('/')
    products_next_page, cache = await Pages.get_next_page(
        cache=await dp.bot.get_cache(username=call.from_user.username, cache_key=CACHE_KEY),
        delete_or_add=InlineKeyboard.add_to_basket
    )

    cache = await Service.object_right(
        dp=dp,
        call=call,
        products_next_page=products_next_page,
        pages=int(pages),
        current_page=int(current_page),
        cache=cache,
        object=Service.product_object
    )

    logging.info(f'SWITCHED NEXT PAGE INTO {call.from_user.username} CHAT')

    await dp.bot.set_cache(username=call.from_user.username, cache_key=CACHE_KEY, cache=cache)
