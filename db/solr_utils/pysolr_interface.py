from abc import ABC, abstractmethod
from typing import List, Dict, Any

class SolrClientInterface(ABC):
    @abstractmethod
    def add(self, documents: List[Dict[str, Any]]):
        pass

    @abstractmethod
    def commit(self, softCommit: bool = True):
        pass

    @abstractmethod
    def search(self, *args, **kwargs):
        pass