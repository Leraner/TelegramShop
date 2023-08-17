import os

from dotenv import load_dotenv

load_dotenv()


CACHE_KEYS = {
    'products': ':products',
    'basket': ':basket'
}
CACHE_KEY_LIVE = [None]
API_TOKEN = os.getenv('API_TOKEN')
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
