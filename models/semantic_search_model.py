from db.services.interfaces.semantic_search_service_interface import (
    SemanticSearchServiceInterface,
)
from db.utils.exceptions import SolrValidationError


class SemanticSearchModel:

    def __init__(self, semantic_search_service_obj: SemanticSearchServiceInterface):
        self._semantic_search_obj = semantic_search_service_obj

    def semantic_search(self, q: str, threshold: float = 0.0) -> list[dict]:
        self._query_valid(q=q)

        return self._semantic_search_obj.semantic_search(
            q=q.lower(), threshold=threshold
        )

    def get_rows_count(self):
        return self._semantic_search_obj.get_rows_count()

    def _query_valid(self, q: str) -> bool:
        if len(q.strip()) < 4:
            raise SolrValidationError("Search query must be at least 4 letters")

        if any(char.isdigit() for char in q):
            raise SolrValidationError("Search query must be only english letters")
