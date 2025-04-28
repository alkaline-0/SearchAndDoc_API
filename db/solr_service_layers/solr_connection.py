from urllib.parse import urljoin

import pysolr

from db.helpers.interfaces.sentence_transformer_interface import (
    SentenceTransformerInterface,
)
from db.solr_service_layers.interfaces.solr_connection_interface import (
    SolrConnectionInterface,
)
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

    def __init__(self, cfg: SolrConfig) -> None:
        self._admin_client = SolrAdminClient(cfg=cfg)
        self.cfg = cfg

    def _get_connection_obj(self, collection_name: str) -> pysolr.Solr:
        if self._admin_client.collection_exist(collection_name):
            collection_url = urljoin(self.cfg.BASE_URL, collection_name)
        else:
            collection_url = self._admin_client.create_collection(
                collection_name=collection_name, num_shards=10
            )
        return pysolr.Solr(
            url=collection_url,
            timeout=18000,
            auth=(self.cfg.USER_NAME, self.cfg.PASSWORD),
            always_commit=True,
        )

    def get_search_client(
        self,
        collection_name: str,
        rerank_model: SentenceTransformerInterface,
        retriever_model: SentenceTransformerInterface,
    ) -> SolrSearchCollectionClient:
        """Get client for specific collection."""

        return SolrSearchCollectionClient(
            solr_client=self._get_connection_obj(collection_name),
            retriever_model=retriever_model,
            rerank_model=rerank_model,
            cfg=self.cfg,
            collection_name=collection_name,
        )

    def get_index_client(
        self, collection_name: str, retriever_model: SentenceTransformerInterface
    ) -> SolrIndexCollectionClient:
        """Get client for specific collection."""
        return SolrIndexCollectionClient(
            solr_client=self._get_connection_obj(collection_name),
            retriever_model=retriever_model,
        )

    def delete_all_collections(self) -> None:
        """Delete all collections."""
        self._admin_client.delete_all_collections()
