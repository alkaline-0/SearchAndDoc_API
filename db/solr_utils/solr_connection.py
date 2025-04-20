from urllib.parse import urljoin
from db.solr_utils.solr_admin import SolrAdminClient
from db.solr_utils.solr_client import SolrCollectionClient
from db.solr_utils.solr_config import SolrConfig


class SolrConnection:
    """Manages Solr connection and client creation."""

    def __init__(self) -> None:
        self._admin_client = SolrAdminClient()

    def get_collection_client(self, collection_name: str) -> SolrCollectionClient:
        """Get client for specific collection."""
        if self._admin_client.collection_exist(collection_name):
            collection_url = urljoin(SolrConfig.BASE_URL, collection_name)
        else:
            collection_url = self._admin_client.create_collection(
                collection_name=collection_name
            )
        return SolrCollectionClient(collection_conn=collection_url)

    def delete_all_collections(self) -> None:
        """Delete all collections."""
        self._admin_client.delete_all_collections()