from db.config.solr_config import SolrConfig
from db.utils.exceptions import SolrConnectionError, SolrValidationError
from models.base_model import BaseModel


class SolrCollectionModel(BaseModel):
    def __init__(self, cfg: SolrConfig):
        self._validate_credentials(cfg)
        _conn_obj = super().get_connection_object(cfg)

        self.solr_admin_obj = _conn_obj.get_admin_client()

    def create_collection(
        self, collection_name: str, num_shards: int = 10, replicas_count: int = 2
    ) -> str:
        if not collection_name:
            raise SolrValidationError("Collection name cannot be empty")
        if num_shards <= 0 or replicas_count <= 0:
            raise SolrValidationError(
                "Number of shards and replicas count must be greater than 0"
            )
        if self.collection_exist(collection_name):
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

    def _validate_credentials(self, cfg) -> None:
        """Handles None, empty strings, and whitespace."""
        if cfg.USER_NAME is None or cfg.PASSWORD is None:
            raise SolrValidationError("Username/password cannot be None")

        if not cfg.USER_NAME.strip() or not cfg.PASSWORD.strip():
            raise SolrValidationError(
                "Username/password cannot be empty or whitespace-only"
            )
