import datetime
import re

import ray
from solrq import Value

from db.services.interfaces.semantic_search_service_interface import (
    SemanticSearchServiceAttrs,
    SemanticSearchServiceInterface,
)
from db.utils.encode import create_embeddings
from db.utils.exceptions import SolrError


class SemanticSearchService(SemanticSearchServiceInterface):
    def __init__(self, attributes: SemanticSearchServiceAttrs) -> None:
        self.solr_client = attributes.solr_client
        self.rerank_model = attributes.rerank_model
        self.retriever_model = attributes.retriever_model
        self.cfg = attributes.cfg
        self.collection_name = attributes.collection_name
        self._logger = attributes.logger
        self.retriever_strategy = attributes.retriever_strategy
        self.reranker_strategy = attributes.reranker_strategy
        self.http_client = attributes.http_client

    def semantic_search(
        self,
        q: str,
        channel_id: int,
        threshold: float = 0.0,
        start_date: datetime.datetime = None,
        end_date: datetime.datetime = None,
    ) -> list[dict]:
        if self._is_malicious(q):
            self._logger.error(f"Query contains invalid characters {q}")
            raise SolrError("Cannot perform this query")

        safe_q = self._build_safe_query(raw_query=q)
        retriever_future = create_embeddings.remote(
            model=self.retriever_model, sentences=[safe_q], normalize_embeddings=False
        )

        self._logger.info("Created the embeddings for the query.")

        [docs] = self.retriever_strategy.retrieve(
            embedding=ray.get(retriever_future),
            total_rows=self.get_rows_count(),
            channel_id=channel_id,
            start_date=start_date,
            end_date=end_date,
        )

        self._logger.info("Retrieved docs from solr successfully.")

        candidate_texts = []
        for item in docs:
            candidate_texts.append(item["message_content"])

        query_rerank_future = create_embeddings.remote(
            model=self.rerank_model, sentences=[safe_q], normalize_embeddings=True
        )

        candidate_futures = create_embeddings.remote(
            model=self.rerank_model,
            sentences=candidate_texts,
            normalize_embeddings=True,
        )

        query_embedding = ray.get(query_rerank_future)
        candidate_embeddings = ray.get(candidate_futures)

        sorted_reranking_results = self.reranker_strategy.rerank(
            query_embedding=query_embedding,
            candidate_embeddings=candidate_embeddings,
            docs=docs,
        )

        self._logger.info("Reranked results from solr successfully.")

        return [item[0] for item in sorted_reranking_results if item[1] >= threshold]

    def _build_safe_query(self, raw_query) -> str:
        return str(Value(raw_query))

    def _is_malicious(self, query: str) -> bool:
        patterns = [
            r"drop\s",
            r"delete\s",
            r";\s*--",
            r"\b(shutdown|truncate)\b",
            r"(?i)(drop|delete|alter)",
        ]
        return any(re.search(pattern, query, re.IGNORECASE) for pattern in patterns)

    def get_rows_count(self) -> int:
        try:
            rows_count_resp = self.http_client.send_request(
                url=f"{self.cfg.BASE_URL}{self.collection_name}/select?indent=on&q=*:*&wt=json&rows=0",
                params={},
            )
            return rows_count_resp["response"]["numFound"]
        except Exception as e:
            self._logger.error(e, stack_info=True, exc_info=True)
            raise e
