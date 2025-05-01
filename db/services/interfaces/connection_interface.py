from abc import ABC, abstractmethod

from db.services.interfaces.collection_admin_interface import CollectionAdminInterface
from db.services.interfaces.indexing_data_service_interface import (
    IndexingDataServiceInterface,
)
from db.services.interfaces.semantic_search_service_interface import (
    SemanticSearchServiceInterface,
)
from db.utils.interfaces.sentence_transformer_interface import (
    SentenceTransformerInterface,
)


class ConnectionInterface(ABC):
    """Interface for Solr connection and client creation."""

    @abstractmethod
    def get_search_client(
        self,
        collection_name: str,
        collection_url: str,
        rerank_model: SentenceTransformerInterface,
        retriever_model: SentenceTransformerInterface,
    ) -> SemanticSearchServiceInterface:
        """Get client for specific collection."""

    @abstractmethod
    def get_index_client(
        self, retriever_model: SentenceTransformerInterface, collection_url: str
    ) -> IndexingDataServiceInterface:
        """Get client for specific collection."""

    @abstractmethod
    def get_admin_client(self) -> CollectionAdminInterface:
        """Get admin client"""
