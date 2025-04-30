from abc import ABC, abstractmethod

from db.solr_service_layers.interfaces.solr_admin_interface import SolrAdminInterface
from db.solr_service_layers.interfaces.solr_index_interface import SolrIndexInerface
from db.solr_service_layers.solr_index_collection_client import SolrIndexCollectionClient


class SolrSearchInterface(ABC):
    """Interface for Solr connection and client creation."""

    @abstractmethod
    def semantic_search(
        self,
        q: str,
        threshold: float,
    ) -> list[dict]:
      pass
    
    @abstractmethod
    def retrieve_all_docs(self) -> list:
      pass

    @abstractmethod
    def get_admin_client(self)->SolrAdminInterface:
        """Get admin client"""
