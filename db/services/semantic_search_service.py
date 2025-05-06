import datetime
import re
from logging import Logger

import ray
from sentence_transformers import util
from solrq import Value

from db.config.solr_config import SolrConfig
from db.services.interfaces.semantic_search_service_interface import (
    SemanticSearchServiceInterface,
)
from db.utils.encode import create_embeddings
from db.utils.exceptions import SolrError
from db.utils.interfaces.pysolr_interface import SolrClientInterface
from db.utils.interfaces.sentence_transformer_interface import (
    SentenceTransformerInterface,
)
from db.utils.request import request


class SemanticSearchService(SemanticSearchServiceInterface):
    def __init__(
        self,
        logger: Logger,
        solr_client: SolrClientInterface,
        retriever_model: SentenceTransformerInterface,
        rerank_model: SentenceTransformerInterface,
        cfg: SolrConfig,
        collection_name: str,
    ) -> None:
        """Creates a new semantic search service object.

        Args:
            solr_client: SolrClientInterface object for Solr operations
            retriever_model: SentenceTransformerInterface for retrieval
            rerank_model: SentenceTransformerInterface for re-ranking
            cfg: configurations for solr connection
            collection_name: name of the collection to perform search on

        Returns: None

        Raises:
            SolrError: for malicious queries
        """

        self.solr_client = solr_client
        self.rerank_model = rerank_model
        self.retriever_model = retriever_model
        self.cfg = cfg
        self.collection_name = collection_name
        self._logger = logger

    def semantic_search(
        self,
        q: str,
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

        [docs] = self._retrieve_docs_with_knn(
            embedding=ray.get(retriever_future),
            total_rows=self.get_rows_count(),
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

        sorted_reranking_results = self._process_reranked_results(
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

    def _retrieve_docs_with_knn(
        self, embedding: list, total_rows: int, start_date: datetime, end_date: datetime
    ) -> list:
        """Ray-optimized parallel fetching for large result sets"""
        chunk_size = 5000
        futures = []
        knn_q = "{!knn f=bert_vector}" + str([float(w) for w in embedding[0]])
        for start in range(0, total_rows, chunk_size):
            actual_rows = min(chunk_size, total_rows - start)
            batch_res = self._fetch_results_in_chunks_with_date(
                q=knn_q,
                start=start,
                rows_count=actual_rows,
                start_date=start_date,
                end_date=end_date,
            )

            if len(batch_res) > 0:
                futures.append(batch_res)

        return futures

    def _fetch_results_in_chunks_with_date(
        self,
        start: int,
        q: str,
        rows_count: int,
        start_date: datetime.datetime = None,
        end_date: datetime.datetime = None,
    ) -> list:
        """Fetch search results in paginated chunks with date filtering."""
        try:
            solr_date_format = "%Y-%m-%dT%H:%M:%SZ"

            if not start_date or not end_date:
                return self._fetch_results_in_chunks(
                    start=start, q=q, rows_count=rows_count
                )

            params = {
                "q": q,
                "start": start,
                "fl": "message_id, message_content, author_id, channel_id, created_at",
                "rows": rows_count,
                "sort": "score desc, message_id asc",
                "fq": f"(created_at:[{start_date.strftime(solr_date_format)} TO {end_date.strftime(solr_date_format)}] OR (*:* NOT created_at:[* TO *]))",
            }
            params = {k: v for k, v in params.items() if v is not None}

            query_exec = self.solr_client.search(**params)
            return query_exec.docs
        except Exception as e:
            self._logger.error(
                f"Failed to fetch chunk {start}-{start+rows_count}: {str(e)}",
                exc_info=True,
                stack_info=True,
            )
            raise

    def _rerank_knn_results(
        self, query_embedding, candidate_embeddings, solr_response: dict
    ):
        """Re-ranks KNN results using semantic similarity.
        Args:
            query: Query string
            solr_response: Solr response containing KNN results
        Returns:
            List of tuples containing re-ranked results
        """
        scores = util.cos_sim(query_embedding, candidate_embeddings)[0].cpu().tolist()

        return sorted(
            zip(
                solr_response,
                scores,
            ),
            key=lambda x: x[1],
            reverse=True,
        )

    def get_rows_count(self) -> int:
        try:
            rows_count_resp = request(
                url=f"{self.cfg.BASE_URL}{self.collection_name}/select?indent=on&q=*:*&wt=json&rows=0",
                cfg=self.cfg,
                params={},
                logger=self._logger,
            )
            return rows_count_resp["response"]["numFound"]
        except Exception as e:
            self._logger.error(e, stack_info=True, exec_info=True)
            raise e

    def _process_reranked_results(
        self, query_embedding, candidate_embeddings, docs
    ) -> list[tuple]:
        """Efficient result processing with tensor operations"""
        scores = util.cos_sim(query_embedding, candidate_embeddings)[0].cpu().tolist()

        return sorted(
            zip(
                docs,
                scores,
            ),
            key=lambda x: x[1],
            reverse=True,
        )

    def _fetch_results_in_chunks(self, start: int, q: str, rows_count: int) -> list:
        try:
            params = {
                "q": q,
                "start": start,
                "fl": "message_id, message_content, author_id, channel_id",
                "rows": rows_count,
                "sort": "score desc, message_id asc",
            }
            query_exec = self.solr_client.search(**params)
            return query_exec.docs
        except Exception as e:
            self._logger.error(e, stack_info=True, exec_info=True)
            raise e
