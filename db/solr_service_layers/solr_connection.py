from urllib.parse import urljoin

import pysolr

from db.helpers.sentence_transformer_impl import STSentenceTransformer
from db.solr_service_layers.interfaces.solr_connection_interface import SolrConnectionInterface
from db.solr_service_layers.solr_admin import SolrAdminClient
from db.solr_service_layers.solr_index_collection_client import SolrIndexCollectionClient
from db.solr_utils.solr_config import SolrConfig


class SolrConnection(SolrConnectionInterface):
    """Manages Solr connection and client creation."""

    def __init__(self, cfg: SolrConfig) -> None:
        super().__init__()
        self._admin_client = SolrAdminClient(cfg=cfg)
        self.cfg = cfg

    def get_collection_client(self, collection_name: str) -> SolrIndexCollectionClient:
        """Get client for specific collection."""
        if self._admin_client.collection_exist(collection_name):
            collection_url = urljoin(self.cfg.BASE_URL, collection_name)
        else:
            collection_url = self._admin_client.create_collection(
                collection_name=collection_name
            )
        solr_client = pysolr.Solr(
            url=collection_url,
            timeout=10,
            auth=(self.cfg.USER_NAME, self.cfg.PASSWORD),
            always_commit=True,
        )
        retriever_model = STSentenceTransformer(
            self.cfg.RETRIEVER_MODEL_NAME, device="mps"
        )
        rerank_model = STSentenceTransformer(self.cfg.RERANK_MODEL_NAME, device="mps")

        return SolrIndexCollectionClient(
            solr_client=solr_client,
            retriever_model=retriever_model,
            rerank_model=rerank_model,
            cfg=self.cfg,
            collection_name=collection_name,
        )

    def delete_all_collections(self) -> None:
        """Delete all collections."""
        self._admin_client.delete_all_collections()
