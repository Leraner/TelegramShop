import logging

from elasticsearch import AsyncElasticsearch, BadRequestError

from actions.actions import ElasticSearchActions
from search.pagination import SearchPaginationProducts
from serializers import SearchSerializerProduct


class ElasticSearchClient(ElasticSearchActions):
    pagination_class = SearchPaginationProducts
    serializer_class = SearchSerializerProduct

    def __init__(self, indices: dict, elastic_hosts: str) -> None:
        self.client = AsyncElasticsearch(elastic_hosts)
        self.base_indices = indices

    async def create_index(self) -> None:
        """
        This method create indices in elasticsearch.
        If index does not exist, create it, if exists, nothing do
        """
        for index in self.base_indices:
            try:
                await self.client.indices.create(
                    index=index,
                    settings=self.base_indices[index]['settings'],
                    mappings=self.base_indices[index]['mappings']
                )
                logging.info(f'INDEX {index} CREATED')
            except BadRequestError:
                pass

    async def create_elastic_product(self, product) -> bool:
        """
        This method create product in elastic
        """
        document = {
            "product_id": product.product_id,
            "name": product.name,
            "description": product.description,
            "image_path": product.image_path,
            "created_date": product.created_date,
            "category_id": product.category_id
        }
        await self.client.index(index="product", document=document)
        logging.info(f"CREATED NEW DOCUMENT {document}")
        return True

    async def search_elastic_products(self, search_request: str) -> list[list]:
        """
        This method search document in elasticsearch by search_request
        """
        query = {
            "bool": {
                "should": [
                    {
                        "wildcard": {
                            "name": {
                                "value": f"*{search_request}*",
                                "boost": 2,
                                "rewrite": "constant_score"
                            }
                        }
                    },
                    {
                        "match": {
                            "name": {
                                "query": f"{search_request}",
                                "operator": "and",
                                "fuzziness": 1
                            }
                        }
                    }
                ]
            }
        }
        res = await self.client.search(index='product', query=query)
        logging.info(f'DOCUMENTS FOUND ON REQUEST: {search_request}')
        return await self.paginated_objects(await self.serialize(res.raw['hits']['hits']))
