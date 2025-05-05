from abc import ABC, abstractmethod
from logging import Logger


class IndexDataServiceInterface(ABC):
    """Interface for Solr connection and client creation."""

    @abstractmethod
    def __init__(self, logger: Logger = None):
        pass

    @abstractmethod
    def index_data(self, data: list[dict], soft_commit: bool) -> None:
        pass
