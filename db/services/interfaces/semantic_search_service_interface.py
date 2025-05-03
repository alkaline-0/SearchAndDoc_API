from abc import ABC, abstractmethod


class SemanticSearchServiceInterface(ABC):
    """Interface for Solr connection and client creation."""

    @abstractmethod
    def semantic_search(
        self,
        q: str,
        threshold: float,
    ) -> list[dict]:
        pass
