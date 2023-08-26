from aiogram.dispatcher.filters.state import StatesGroup, State


class ProductState(StatesGroup):
    """State for creation product"""
    START_CREATION = State()
    NAME = State()
    DESCRIPTION = State()
    IMAGE_PATH = State()
    CATEGORY = State()


class SearchProductState(StatesGroup):
    SEARCH_REQUEST = State()
