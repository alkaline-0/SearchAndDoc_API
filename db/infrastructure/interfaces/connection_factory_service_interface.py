from abc import ABC, abstractmethod
from logging import Logger

from db.data_access.interfaces.collection_admin_service_interface import (
    CollectionAdminServiceInterface,
)
from db.services.interfaces.index_data_service_interface import (
    IndexDataServiceInterface,
)
from db.services.interfaces.semantic_search_service_interface import (
    SemanticSearchServiceInterface,
)
from db.utils.interfaces.sentence_transformer_interface import (
    SentenceTransformerInterface,
)


class ConnectionFactoryServiceInterface(ABC):
    """Interface for Solr connection and client creation."""

    @abstractmethod
    def __init__(self, logger: Logger):
        pass

    @abstractmethod
    def get_search_client(
        self,
        collection_name: str,
        retriever_model: SentenceTransformerInterface,
        rerank_model: SentenceTransformerInterface,
        collection_url: str,
    ) -> SemanticSearchServiceInterface:
        pass

    @abstractmethod
    def get_index_client(
        self, retriever_model: SentenceTransformerInterface, collection_url: str
    ) -> IndexDataServiceInterface:
        pass

    @abstractmethod
    def get_admin_client(self) -> CollectionAdminServiceInterface:
        pass
