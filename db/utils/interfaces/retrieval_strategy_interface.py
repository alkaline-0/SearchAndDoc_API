from abc import ABC, abstractmethod


class RetrievalStrategy(ABC):
    @abstractmethod
    def retrieve(
        self, query_embedding: list, channel_id: int, total_rows: int, **kwargs
    ) -> list[dict]:
        pass
