from abc import ABC, abstractmethod


class IndexDataServiceInterface(ABC):
    """Interface for Solr connection and client creation."""

    @abstractmethod
    def index_data(self, data: list[dict], soft_commit: bool) -> None:
        pass
