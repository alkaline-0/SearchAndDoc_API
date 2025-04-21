from urllib.parse import urljoin

import pysolr
from sentence_transformers import SentenceTransformer

from db.solr_utils.solr_admin import SolrAdminClient
from db.solr_utils.solr_client import SolrCollectionClient
from db.solr_utils.solr_config import SolrConfig


class SolrConnection:
    """Manages Solr connection and client creation."""

    def __init__(self, cfg: SolrConfig) -> None:
        self._admin_client = SolrAdminClient(cfg=cfg)
        self.cfg = cfg

    def get_collection_client(self, collection_name: str) -> SolrCollectionClient:
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
            retriever_model = SentenceTransformer(self.cfg.RETRIEVER_MODEL_NAME)
            rerank_model = SentenceTransformer(self.cfg.RERANK_MODEL_NAME)

            return SolrCollectionClient(
                solr_client=solr_client,
                retriever_model=retriever_model,
                rerank_model=rerank_model,
            )

    def delete_all_collections(self) -> None:
        """Delete all collections."""
        self._admin_client.delete_all_collections()
