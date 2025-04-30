import re

import ray
from sentence_transformers import util
from solrq import Value

from db.helpers.encode import create_embeddings
from db.helpers.interfaces.sentence_transformer_interface import (
    SentenceTransformerInterface,
)
from db.helpers.solr_request import make_solr_request
from db.solr_service_layers.interfaces.solr_search_interface import SolrSearchInterface
from db.solr_utils.interfaces.pysolr_interface import SolrClientInterface
from db.solr_utils.solr_config import SolrConfig
from db.solr_utils.solr_exceptions import SolrError


class SolrSearchCollectionClient(SolrSearchInterface):
    def __init__(
        self,
        solr_client: SolrClientInterface,
        retriever_model: SentenceTransformerInterface,
        rerank_model: SentenceTransformerInterface,
        cfg: SolrConfig,
        collection_name: str,
    ) -> None:
        """Creates a new Solr collection agent.

        Args:
            solr_client: SolrClientInterface object for Solr operations
            retriever_model: SentenceTransformerInterface for retrieval
            rerank_model: SentenceTransformerInterface for re-ranking

        Returns: None

        Raises:
            ValueErrorException: for any missing params
        """

        self.solr_client = solr_client
        self.rerank_model = rerank_model
        self.retriever_model = retriever_model
        self.cfg = cfg
        self.collection_name = collection_name

    def semantic_search(
        self,
        q: str,
        threshold: float = 0.1,
    ) -> list[dict]:
        safe_q = self._build_safe_query(raw_query=q)
        if self._is_malicious(q):
            raise SolrError("Cannot perform this query")

        # Parallel embedding generation for retrieval for the query
        retriever_future = create_embeddings.remote(
            model=self.retriever_model, sentences=[safe_q], normalize_embeddings=False
        )

        # Phase 1: Retrieve initial candidates (optimized Solr query)
        [docs] = self._retrieve_docs_with_knn(
            embedding=ray.get(retriever_future), total_rows=self._get_rows_count()
        )

        candidate_texts = []
        for item in docs:
            candidate_texts.append(item["message_content"])

        # Parallel re-ranking phase
        query_rerank_future = create_embeddings.remote(
            model=self.rerank_model, sentences=[safe_q], normalize_embeddings=True
        )

        candidate_futures = create_embeddings.remote(
            model=self.rerank_model,
            sentences=candidate_texts,
            normalize_embeddings=True,
        )

        # Process results as they complete
        query_embedding = ray.get(query_rerank_future)
        candidate_embeddings = ray.get(candidate_futures)
        # Re-rank and filter results
        sorted_reranking_results = self._process_reranked_results(
            query_embedding=query_embedding,
            candidate_embeddings=candidate_embeddings,
            docs=docs,
        )

        return [
            item[0]
            for item in sorted_reranking_results
            if round(item[1], 2) >= threshold
        ]

    def _build_safe_query(self, raw_query) -> str:
        return str(Value(raw_query))

    def retrieve_all_docs(self) -> list:
        """Ray-optimized parallel fetching for large result sets"""
        chunk_size = 5000
        futures = []
        total_rows = self._get_rows_count()
        for start in range(0, total_rows, chunk_size):
            actual_rows = min(chunk_size, total_rows - start)
            batch_res = self._fetch_results_in_chunks(
                q="*:*", start=start, rows_count=actual_rows
            )

            if len(batch_res) > 0:
                futures.append(batch_res)

        return futures

    def _is_malicious(self, query: str) -> bool:
        patterns = [
            r"drop\s",  # Catches "DROP TABLE", "DROP COLLECTION"
            r"delete\s",
            r";\s*--",  # SQL-style comments
            r"\b(shutdown|truncate)\b",
            r"(?i)(drop|delete|alter)",  # Case-insensitive
        ]
        return any(re.search(pattern, query, re.IGNORECASE) for pattern in patterns)

    def _retrieve_docs_with_knn(self, embedding: list, total_rows: int) -> list:
        """Ray-optimized parallel fetching for large result sets"""
        chunk_size = 5000
        futures = []
        knn_q = "{!knn f=bert_vector topK=200}" + str([float(w) for w in embedding[0]])
        for start in range(0, total_rows, chunk_size):
            actual_rows = min(chunk_size, total_rows - start)
            batch_res = self._fetch_results_in_chunks(
                q=knn_q, start=start, rows_count=actual_rows
            )

            if len(batch_res) > 0:
                futures.append(batch_res)

        return futures

    def _fetch_results_in_chunks(self, start: int, q: str, rows_count: int) -> list:
        params = {
            "q": q,
            "start": start,
            "fl": "message_id, message_content, author_id, channel_id",
            "rows": rows_count,
            "sort": "score desc, message_id asc",
        }
        return self.solr_client.search(**params).docs

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
        # Cosine similarity between query and each candidate
        scores = util.cos_sim(query_embedding, candidate_embeddings)[0].cpu().tolist()

        # Zip together for sorting
        return sorted(
            zip(
                solr_response,
                scores,
            ),
            key=lambda x: x[1],
            reverse=True,
        )

    def _get_rows_count(self) -> int:
        rows_count_resp = make_solr_request(
            url=f"{self.cfg.BASE_URL}{self.collection_name}/select?indent=on&q=*:*&wt=json&rows=0",
            cfg=self.cfg,
            params={},
        )
        return rows_count_resp["response"]["numFound"]

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
