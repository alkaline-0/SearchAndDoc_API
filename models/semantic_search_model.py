from db.config.solr_config import SolrConfig
from db.utils.exceptions import SolrValidationError
from db.utils.interfaces.sentence_transformer_interface import (
    SentenceTransformerInterface,
)
from models.base_model import BaseModel


class SemanticSearchModel(BaseModel):

    def __init__(
        self,
        cfg: SolrConfig,
        collection_name: str,
        collection_url: str,
        retriever_model: SentenceTransformerInterface,
        rerank_model: SentenceTransformerInterface,
    ):
        _conn_obj = super().get_connection_object(cfg)

        self._semantic_search_obj = _conn_obj.get_search_client(
            collection_url=collection_url,
            rerank_model=rerank_model,
            retriever_model=retriever_model,
            collection_name=collection_name,
        )

    def semantic_search(self, q: str, threshold: float = 0.1) -> list[dict]:
        self._query_valid(q=q)

        return self._semantic_search_obj.semantic_search(
            q=q.lower(), threshold=threshold
        )

    def _query_valid(self, q: str) -> bool:
        if len(q.strip()) < 4:
            raise SolrValidationError("Search query must be at least 4 letters")

        if any(char.isdigit() for char in q):
            raise SolrValidationError("Search query must be only english letters")

    def retrieve_all_docs(self) -> list:
        return self._semantic_search_obj.retrieve_all_docs()
