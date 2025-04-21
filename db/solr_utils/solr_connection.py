from urllib.parse import urljoin

from db.solr_utils.solr_admin import SolrAdminClient
from db.solr_utils.solr_client import SolrCollectionClient
from db.solr_utils.solr_config import SolrConfig


class SolrConnection:
    """Manages Solr connection and client creation."""

    def __init__(self, cfg: SolrConfig) -> None:
        self._admin_client = SolrAdminClient()
        self.cfg = cfg

    def get_collection_client(self, collection_name: str) -> SolrCollectionClient:
        """Get client for specific collection."""
        if self._admin_client.collection_exist(collection_name):
            collection_url = urljoin(self.cfg.BASE_URL, collection_name)
        else:
            collection_url = self._admin_client.create_collection(
                collection_name=collection_name
            )
            solr_session = self._admin_client.create_solr_session(
                collection_url=collection_url
            )
        return SolrCollectionClient(solr_session, self.cfg)

    def delete_all_collections(self) -> None:
        """Delete all collections."""
        self._admin_client.delete_all_collections()
