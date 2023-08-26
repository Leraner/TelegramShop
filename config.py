import os

from dotenv import load_dotenv

from search.mappings import MAPPING_FOR_PRODUCT_INDEX, SETTINGS_FOR_PRODUCT_INDEX

load_dotenv()

API_TOKEN = os.getenv('API_TOKEN')
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
DSN = os.getenv('DSN')

elastic_hosts = "http://localhost:9200"
ELASTIC_INDICES = {
    'product': {
        "mappings": MAPPING_FOR_PRODUCT_INDEX,
        "settings": SETTINGS_FOR_PRODUCT_INDEX
    }
}
