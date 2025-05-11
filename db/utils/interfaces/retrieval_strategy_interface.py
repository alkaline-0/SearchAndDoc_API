from abc import ABC, abstractmethod

class RetrievalStrategy(ABC):
    @abstractmethod
    def retrieve(self, query_embedding: list, total_rows: int, **kwargs) -> list[dict]:
        pass