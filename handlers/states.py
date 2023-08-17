from aiogram.dispatcher.filters.state import StatesGroup, State


class ProductState(StatesGroup):
    START_CREATION = State()
    NAME = State()
    DESCRIPTION = State()
    IMAGE_PATH = State()