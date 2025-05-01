from abc import ABC, abstractmethod


class CollectionAdminInterface(ABC):
    """Interface for Solr connection and client creation."""

    @abstractmethod
    def create_collection(
        self, collection_name: str, num_shards: int = 1, replica_count: int = 2
    ) -> str:
        pass

    @abstractmethod
    def delete_all_collections(self) -> dict:
        pass

    @abstractmethod
    def collection_exist(self, collection_name: str) -> bool:
        pass
