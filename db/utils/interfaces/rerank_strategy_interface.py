from abc import ABC, abstractmethod


class RerankStrategy(ABC):
    @abstractmethod
    def rerank(
        self, query_embedding: list, candidate_embeddings: list, docs: list[dict]
    ) -> list[tuple[dict, float]]:
        pass
