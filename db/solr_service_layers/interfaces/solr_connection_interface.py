from abc import ABC


class SolrConnectionInterface(ABC):
    """Interface for Solr connection and client creation."""

    def get_collection_client(self, collection_name: str):
        """Get client for specific collection."""
        raise NotImplementedError

    def delete_all_collections(self) -> None:
        """Delete all collections."""
        raise NotImplementedError