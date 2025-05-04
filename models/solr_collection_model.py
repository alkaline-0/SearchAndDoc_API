from logging import Logger

from db.services.interfaces.collection_admin_service_interface import (
    CollectionAdminServiceInterface,
)
from db.utils.exceptions import SolrConnectionError, SolrValidationError


class SolrCollectionModel:
    def __init__(
        self,
        collection_admin_service_obj: CollectionAdminServiceInterface,
        logger: Logger,
    ):
        self.solr_admin_obj = collection_admin_service_obj
        self._logger = logger

    def create_collection(
        self, collection_name: str, num_shards: int = 10, replicas_count: int = 2
    ) -> str:
        if not collection_name:
            self._logger.error("Invalid collection name None")
            raise SolrValidationError("Collection name cannot be empty")
        if num_shards <= 0 or replicas_count <= 0:
            self._logger.error("Invalid number of shards or replica count")
            raise SolrValidationError(
                "Number of shards and replicas count must be greater than 0"
            )
        if self.collection_exist(collection_name):
            self._logger.error(
                f"Attempting to create a collection with an existing name {collection_name}"
            )
            raise SolrConnectionError(
                "Cannot create a collection with the same name as existing one"
            )

        return self.solr_admin_obj.create_collection(
            collection_name=collection_name,
            num_shards=num_shards,
            replica_count=replicas_count,
        )

    def delete_all_collections(self) -> None:
        return self.solr_admin_obj.delete_all_collections()

    def collection_exist(self, collection_name: str) -> bool:
        return self.solr_admin_obj.collection_exist(collection_name=collection_name)
