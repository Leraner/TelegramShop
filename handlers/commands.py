import datetime

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ContentType
from sqlalchemy.ext.asyncio import AsyncSession

from actions.basket_actions import BasketActions
from actions.user_actions import UserActions
from exceptions.exceptions import PermissionDenied
from handlers.services import ProductPages
from handlers.states import ProductState
from keyboards.inline_keyboard import InlineKeyboard
from loader import dp, product_actions

products_pages = ProductPages()


@dp.message_handler(commands=['start'])
async def start_command(message: types.Message, session: AsyncSession) -> None:
    bot_data = await dp.bot.get_me()
    new_user = await UserActions.create_new_user(message=message, session=session)
    await message.answer(f'Hello, {new_user.first_name}, welcome to {bot_data["username"]}')


@dp.message_handler(commands=['test'])
async def test(message: types.Message, session: AsyncSession) -> None:
    user = await UserActions.get_user_by_username(username=message.from_user.username, session=session)
    product = await product_actions.get_product_by_id(product_id=1, session=session)
    new_user = await BasketActions.add_product_to_user_basket(user=user, product=product, session=session)


@dp.message_handler(commands=['create_product'])
async def create_product(message: types.Message, session: AsyncSession, state: FSMContext) -> None:
    await message.answer('Напишите название продукта')
    await state.set_state(ProductState.START_CREATION)


@dp.message_handler(state=ProductState.START_CREATION)
async def create_product_get_name(message: types.Message, session: AsyncSession, state: FSMContext) -> None:
    msg = message.text
    await state.update_data(NAME=msg)
    await message.answer('Напишите описание к продукту')
    await state.set_state(ProductState.DESCRIPTION)


@dp.message_handler(state=ProductState.DESCRIPTION)
async def create_product_get_image(message: types.Message, session: AsyncSession, state: FSMContext) -> None:
    msg = message.text
    await state.update_data(DESCRIPTION=msg)
    await message.answer('Пришлите изображение продукта')
    await state.set_state(ProductState.IMAGE_PATH)


@dp.message_handler(state=ProductState.IMAGE_PATH, content_types=ContentType.PHOTO)
async def create_product_get_image(message: types.Message, session: AsyncSession, state: FSMContext) -> None:
    photo = message.photo[1]
    date = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    path = f'media/products_images/{date}/{date}.png'
    await photo.download(destination_file=path)

    product_state_data = await state.get_data()
    data = {
        'name': product_state_data['NAME'],
        'description': product_state_data['DESCRIPTION'],
        'image_path': path
    }
    try:
        new_product = await product_actions.create_product(
            message=data,
            session=session,
            username=message.from_user.username
        )
    except PermissionDenied as error:
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


@dp.message_handler(commands=['show_products'])
async def show_all_products(message: types.Message, session: AsyncSession) -> None:
    all_products = await product_actions.show_products(session=session)
    products_pages.products = all_products

    for product in all_products[0]:
        caption = f"""
             <b>{product.name}</b>
             {product.description}
        """
        product_message = await message.answer_photo(
            open(f'{product.image_path}', 'rb'),
            caption=caption,
            parse_mode='HTML'
        )
        products_pages.messages.append(product_message.message_id)

    tab_message = await message.answer('Переключалка',
                                       reply_markup=await InlineKeyboard.generate_keyboard(1, len(all_products))
                                       )
    products_pages.tab_message_id = tab_message.message_id


@dp.callback_query_handler(text=['<'])
async def left(call: types.CallbackQuery) -> None:
    current_page, pages = call.message.reply_markup.inline_keyboard[0][1].text.split('/')
    products_previous_page = products_pages.get_previous_page()

    if products_previous_page is None:
        return

    if len(products_previous_page['create']) > 0:
        await dp.bot.delete_message(chat_id=call.message.chat.id, message_id=products_pages.tab_message_id)

    for form in products_previous_page['post']:
        await dp.bot.edit_message_media(chat_id=call.message.chat.id, **form)
    for form in products_previous_page['create']:
        new_message = await dp.bot.send_photo(chat_id=call.message.chat.id, **form)
        products_pages.messages.append(new_message.message_id)

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

    products_pages.tab_message_id = tab_message.message_id


@dp.callback_query_handler(text=['>'])
async def right(call: types.CallbackQuery) -> None:
    current_page, pages = call.message.reply_markup.inline_keyboard[0][1].text.split('/')
    products_next_page = products_pages.get_next_page()

    if products_next_page is None:
        return

    for form in products_next_page['post']:
        await dp.bot.edit_message_media(chat_id=call.message.chat.id, **form)
    for message in products_next_page['delete']:
        await dp.bot.delete_message(chat_id=call.message.chat.id, message_id=message)

    tab_message = await call.message.edit_reply_markup(
        await InlineKeyboard.generate_keyboard(int(current_page) + 1, pages)
    )
    products_pages.tab_message_id = tab_message.message_id
