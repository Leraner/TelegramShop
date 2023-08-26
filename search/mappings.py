MAPPING_FOR_PRODUCT_INDEX = {
    "properties": {
        "product_id": {
            "type": "integer",
            "coerce": "false",
            "fields": {
                "keyword": {
                    "type": "keyword"
                }
            }
        },
        "name": {
            "type": "text",
            "analyzer": "my_synonyms",
            "fields": {
                "keyword": {
                    "type": "keyword"
                }
            }
        },
        "description": {
            "type": "text",
            "fields": {
                "keyword": {
                    "type": "keyword"
                }
            }
        },
        "image_path": {
            "type": "text"
        },
        "created_date": {
            "type": "date",
            "format": "yyyy-MM-dd'T'HH:mm:ss.SSSSSS"
        },
        "category_id": {
            "type": "integer",
            "coerce": "false",
            "fields": {
                "keyword": {
                    "type": "keyword"
                }
            }
        }
    }
}

SETTINGS_FOR_PRODUCT_INDEX = {
    "analysis": {
        "filter": {
            "my_synonym_filter": {
                "type": "synonym",
                "synonyms_path": "synonyms.txt",
                "lenient": "true"
            },
            "ru_stop": {
                "type": "stop",
                "stopwords": "_russian_"
            },
            "ru_stemmer": {
                "type": "stemmer",
                "language": "russian"
            }
        },
        "analyzer": {
            "my_synonyms": {
                "tokenizer": "standard",
                "filter": [
                    "lowercase",
                    "my_synonym_filter",
                    "ru_stop",
                    "ru_stemmer"
                ]
            }
        }
    }
}
