import datetime
from abc import ABC, abstractmethod
from logging import Logger


class SemanticSearchServiceInterface(ABC):
    """Interface for Solr connection and client creation."""

    @abstractmethod
    def __init__(self, logger: Logger = None):
        pass

    @abstractmethod
    def semantic_search(
        self,
        q: str,
        threshold: float,
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> list[dict]:
        pass
