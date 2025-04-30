import pysolr

from db.helpers.interfaces.sentence_transformer_interface import (
    SentenceTransformerInterface,
)
from db.solr_service_layers.interfaces.solr_admin_interface import SolrAdminInterface
from db.solr_service_layers.interfaces.solr_connection_interface import (
    SolrConnectionInterface,
)
from db.solr_service_layers.interfaces.solr_index_interface import SolrIndexInerface
from db.solr_service_layers.interfaces.solr_search_interface import SolrSearchInterface
from db.solr_service_layers.solr_admin import SolrAdminClient
from db.solr_service_layers.solr_index_collection_client import (
    SolrIndexCollectionClient,
)
from db.solr_service_layers.solr_search_collection_client import (
    SolrSearchCollectionClient,
)
from db.solr_utils.solr_config import SolrConfig


class SolrConnection(SolrConnectionInterface):
    """Manages Solr connection and client creation."""

    _pysolr_obj: pysolr.Solr

    def __init__(self, cfg: SolrConfig) -> None:
        self.cfg = cfg

    def _get_connection_obj(self, collection_url: str) -> pysolr.Solr:
        if not self._pysolr_obj:
            self._pysolr_obj = pysolr.Solr(
                url=collection_url,
                timeout=300,
                auth=(self.cfg.USER_NAME, self.cfg.PASSWORD),
                always_commit=True,
            )
        return self._pysolr_obj

    def get_admin_client(self) -> SolrAdminInterface:
        return SolrAdminClient(cfg=self.cfg)

    def get_search_client(
        self,
        collection_name: str,
        collection_url: str,
        rerank_model: SentenceTransformerInterface,
        retriever_model: SentenceTransformerInterface,
    ) -> SolrSearchInterface:
        """Get client for specific collection."""

        return SolrSearchCollectionClient(
            solr_client=self._get_connection_obj(collection_url=collection_url),
            retriever_model=retriever_model,
            rerank_model=rerank_model,
            cfg=self.cfg,
            collection_name=collection_name,
        )

    def get_index_client(
        self, retriever_model: SentenceTransformerInterface, collection_url: str
    ) -> SolrIndexInerface:
        return SolrIndexCollectionClient(
            solr_client=self._get_connection_obj(collection_url=collection_url),
            retriever_model=retriever_model,
        )
