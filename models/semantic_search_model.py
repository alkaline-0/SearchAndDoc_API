import datetime
from logging import Logger

from db.services.interfaces.semantic_search_service_interface import (
    SemanticSearchServiceInterface,
)
from db.utils.exceptions import SolrValidationError


class SemanticSearchModel:

    def __init__(
        self,
        semantic_search_service_obj: SemanticSearchServiceInterface,
        logger: Logger,
    ):
        self._semantic_search_obj = semantic_search_service_obj
        self._logger = logger

    def semantic_search(
        self,
        q: str,
        channel_id: int,
        threshold: float = 0.0,
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> list[dict]:
        self._query_valid(q=q)

        return self._semantic_search_obj.semantic_search(
            q=q.lower(),
            channel_id=channel_id,
            threshold=threshold,
            start_date=start_date,
            end_date=end_date,
        )

    def get_rows_count(self):
        return self._semantic_search_obj.get_rows_count()

    def _query_valid(self, q: str) -> bool:
        if len(q.strip()) < 4:
            self._logger.error(f"Invalid Search query: {q}")
            raise SolrValidationError("Search query must be at least 4 letters")

        if any(char.isdigit() for char in q):
            self._logger.error(f"Invalid Search query containing numbers {q}")
            raise SolrValidationError("Search query must be only english letters")
