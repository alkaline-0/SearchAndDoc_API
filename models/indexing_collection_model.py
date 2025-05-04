from logging import Logger

from db.services.interfaces.index_data_service_interface import (
    IndexDataServiceInterface,
)
from db.utils.exceptions import SolrValidationError


class IndexingCollectionModel:
    def __init__(self, indexing_service_obj: IndexDataServiceInterface, logger: Logger):

        self._indexing_client = indexing_service_obj
        self._logger = logger

    def index_data(self, documents: list[dict], soft_commit: bool = True) -> None:
        if len(documents) < 1 or not documents:
            self._logger.error(
                "failed to index documents because length is less than one"
            )
            raise SolrValidationError("Data to index cannot be empty")

        self._indexing_client.index_data(data=documents, soft_commit=soft_commit)
