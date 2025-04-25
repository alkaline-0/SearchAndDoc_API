from abc import ABC, abstractmethod


class SolrConnectionInterface(ABC):
    """Interface for Solr connection and client creation."""

    @abstractmethod
    def get_search_client(self, collection_name: str):
        """Get client for specific collection."""

    @abstractmethod
    def get_index_client(self, collection_name: str):
        """Get client for specific collection."""

    @abstractmethod
    def delete_all_collections(self) -> None:
        """Delete all collections."""
