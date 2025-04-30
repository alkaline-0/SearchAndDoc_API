from abc import ABC, abstractmethod

from db.helpers.interfaces.sentence_transformer_interface import (
    SentenceTransformerInterface,
)
from db.solr_service_layers.interfaces.solr_admin_interface import SolrAdminInterface
from db.solr_service_layers.interfaces.solr_index_interface import SolrIndexInerface
from db.solr_service_layers.interfaces.solr_search_interface import SolrSearchInterface


class SolrConnectionInterface(ABC):
    """Interface for Solr connection and client creation."""

    @abstractmethod
    def get_search_client(
        self,
        collection_name: str,
        collection_url: str,
        rerank_model: SentenceTransformerInterface,
        retriever_model: SentenceTransformerInterface,
    ) -> SolrSearchInterface:
        """Get client for specific collection."""

    @abstractmethod
    def get_index_client(
        self, retriever_model: SentenceTransformerInterface, collection_url: str
    ) -> SolrIndexInerface:
        """Get client for specific collection."""

    @abstractmethod
    def get_admin_client(self) -> SolrAdminInterface:
        """Get admin client"""
