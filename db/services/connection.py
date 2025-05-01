import pysolr

from db.config.solr_config import SolrConfig
from db.services.admin import CollectionAdmin
from db.services.index_data_service import IndexDataService
from db.services.interfaces.collection_admin_interface import CollectionAdminInterface
from db.services.interfaces.connection_interface import ConnectionInterface
from db.services.interfaces.index_data_service_interface import (
    IndexDataServiceInterface,
)
from db.services.interfaces.semantic_search_service_interface import (
    SemanticSearchServiceInterface,
)
from db.services.semantic_search_service import SemanticSearchService
from db.utils.interfaces.sentence_transformer_interface import (
    SentenceTransformerInterface,
)


class ConnectionFactory(ConnectionInterface):
    """Manages Solr connection and client creation."""

    def __init__(self, cfg: SolrConfig) -> None:
        self.cfg = cfg
        self._pysolr_obj = None

    def _get_connection_obj(self, collection_url: str) -> pysolr.Solr:
        if not self._pysolr_obj:
            self._pysolr_obj = pysolr.Solr(
                url=collection_url,
                timeout=300,
                auth=(self.cfg.USER_NAME, self.cfg.PASSWORD),
                always_commit=True,
            )
        return self._pysolr_obj

    def get_admin_client(self) -> CollectionAdminInterface:
        return CollectionAdmin(cfg=self.cfg)

    def get_search_client(
        self,
        collection_name: str,
        collection_url: str,
        rerank_model: SentenceTransformerInterface,
        retriever_model: SentenceTransformerInterface,
    ) -> SemanticSearchServiceInterface:
        """Get client for specific collection."""

        return SemanticSearchService(
            solr_client=self._get_connection_obj(collection_url=collection_url),
            retriever_model=retriever_model,
            rerank_model=rerank_model,
            cfg=self.cfg,
            collection_name=collection_name,
        )

    def get_index_client(
        self, retriever_model: SentenceTransformerInterface, collection_url: str
    ) -> IndexDataServiceInterface:
        return IndexDataService(
            solr_client=self._get_connection_obj(collection_url=collection_url),
            retriever_model=retriever_model,
        )
