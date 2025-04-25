from abc import ABC, abstractmethod


class SolrConnectionInterface(ABC):
    """Interface for Solr connection and client creation."""

    @abstractmethod
    def get_collection_client(self, collection_name: str):
        """Get client for specific collection."""
        raise NotImplementedError

    @abstractmethod
    def delete_all_collections(self) -> None:
        """Delete all collections."""
        raise NotImplementedError
