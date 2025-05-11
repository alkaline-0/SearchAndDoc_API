from logging import Logger

import pysolr

from db.config.solr_config import SolrConfig
from db.data_access.collection_admin_service import CollectionAdminService
from db.data_access.interfaces.collection_admin_service_interface import (
    CollectionAdminServiceInterface,
)
from db.infrastructure.interfaces.connection_factory_service_interface import (
    ConnectionFactoryServiceInterface,
)
from db.services.index_data_service import IndexDataService
from db.services.interfaces.index_data_service_interface import (
    IndexDataServiceInterface,
)
from db.services.interfaces.semantic_search_service_interface import (
    SemanticSearchServiceInterface,
)
from db.services.semantic_search_service import (
    SemanticSearchService,
    SemanticSearchServiceAttrs,
)
from db.utils.cos_similarity_reranker import CosineSimilarityReranker
from db.utils.interfaces.sentence_transformer_interface import (
    SentenceTransformerInterface,
)
from db.utils.solr_knn_search import SolrKnnSearch


class ConnectionFactoryService(ConnectionFactoryServiceInterface):
    """Manages Solr connection and client creation."""

    def __init__(self, cfg: SolrConfig, logger: Logger) -> None:
        self.cfg = cfg
        self._pysolr_obj = None
        self._logger = logger

    def _get_connection_obj(self, collection_url: str) -> pysolr.Solr:
        if not self._pysolr_obj:
            self._pysolr_obj = pysolr.Solr(
                url=collection_url,
                timeout=300,
                auth=(self.cfg.USER_NAME, self.cfg.PASSWORD),
                always_commit=True,
            )
        return self._pysolr_obj

    def get_admin_client(self) -> CollectionAdminServiceInterface:
        return CollectionAdminService(cfg=self.cfg, logger=self._logger)

    def get_search_client(
        self,
        collection_name: str,
        retriever_model: SentenceTransformerInterface,
        rerank_model: SentenceTransformerInterface,
        collection_url: str,
    ) -> SemanticSearchServiceInterface:
        """Get client for specific collection."""
        solr_client = self._get_connection_obj(collection_url=collection_url)
        retriever_strategy = SolrKnnSearch(
            solr_client=solr_client, cfg=self.cfg, logger=self._logger
        )
        rerank_strategy = CosineSimilarityReranker()

        return SemanticSearchService(
            attributes=SemanticSearchServiceAttrs(
                logger=self._logger,
                solr_client=solr_client,
                retriever_model=retriever_model,
                rerank_model=rerank_model,
                cfg=self.cfg,
                collection_name=collection_name,
                retriever_strategy=retriever_strategy,
                reranker_strategy=rerank_strategy,
            )
        )

    def get_index_client(
        self, retriever_model: SentenceTransformerInterface, collection_url: str
    ) -> IndexDataServiceInterface:
        return IndexDataService(
            solr_client=self._get_connection_obj(collection_url=collection_url),
            retriever_model=retriever_model,
            logger=self._logger,
        )
