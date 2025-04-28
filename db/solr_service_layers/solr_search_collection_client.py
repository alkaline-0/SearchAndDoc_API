import re

import ray
import torch
from sentence_transformers import util
from solrq import Value

from db.helpers.encode import create_embeddings
from db.helpers.interfaces.sentence_transformer_interface import (
    SentenceTransformerInterface,
)
from db.helpers.solr_request import make_solr_request
from db.solr_utils.interfaces.pysolr_interface import SolrClientInterface
from db.solr_utils.solr_config import SolrConfig
from db.solr_utils.solr_exceptions import SolrError, SolrValidationError


class SolrSearchCollectionClient:
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
        safe_q = self.build_safe_query(raw_query=q)
        self._validate_search_params(query=safe_q)

        # Parallel embedding generation for retrieval for the query
        retriever_future = create_embeddings.remote(
            self.retriever_model, [safe_q], normalize=False
        )

        # Phase 1: Retrieve initial candidates (optimized Solr query)
        [docs] = self._retrieve_docs_with_knn(
            retriever_embedding=ray.get(retriever_future),
        )

        # Prepare candidate texts for parallel processing
        candidate_texts = [item["message_content"] for item in docs]
        batch_size = 256  # Tune based on GPU memory
        text_batches = [
            candidate_texts[i : i + batch_size]
            for i in range(0, len(candidate_texts), batch_size)
        ]

        # Parallel re-ranking phase
        query_rerank_future = create_embeddings().remote(
            self.rerank_model, [safe_q], normalize=True
        )

        candidate_futures = [
            create_embeddings.remote(self.rerank_model, batch, normalize=True)
            for batch in text_batches
        ]

        # Process results as they complete
        query_embedding = ray.get(query_rerank_future)
        candidate_embeddings = torch.cat(ray.get(candidate_futures), dim=0)

        # Re-rank and filter results
        return self._process_reranked_results(
            query_embedding, candidate_embeddings, docs, threshold
        )

    def build_safe_query(self, raw_query) -> str:
        return str(Value(raw_query))

    def _validate_search_params(self, query: str) -> None:
        """Validate search parameters."""
        if not query:
            raise SolrValidationError("Query string cannot be empty")
        if self._is_malicious(query):
            raise SolrError("Cannot perform this query")

    def _is_malicious(self, query: str) -> bool:
        patterns = [
            r"drop\s",  # Catches "DROP TABLE", "DROP COLLECTION"
            r"delete\s",
            r";\s*--",  # SQL-style comments
            r"\b(shutdown|truncate)\b",
            r"(?i)(drop|delete|alter)",  # Case-insensitive
        ]
        return any(re.search(pattern, query, re.IGNORECASE) for pattern in patterns)

    def _retrieve_docs_with_knn(
        self,
        retriever_embedding,
    ) -> list[list[dict]]:
        """Optimized Solr KNN retrieval with Ray-friendly design"""
        embedding_str = (
            "[" + ",".join(map(str, retriever_embedding[0].cpu().numpy())) + "]"
        )

        # Parallel fetch for very large top_k
        return self._parallel_solr_fetch(embedding_str, rows=self._get_rows_count())

    def _parallel_solr_fetch(self, embedding_str: str, total_rows: int) -> list:
        """Ray-optimized parallel fetching for large result sets"""
        chunk_size = 5000
        futures = []

        for start in range(0, total_rows, chunk_size):
            actual_rows = min(chunk_size, total_rows - start)
            futures.append(
                self._fetch_results_in_chunks(embedding_str, start, actual_rows)
            )

        return ray.get(futures)

    def _fetch_results_in_chunks(
        self, start: int, knn_query: str, rows_count: int
    ) -> list:
        params = {
            "q": knn_query,
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
        self, query_embedding, candidate_embeddings, docs, threshold
    ) -> list[dict]:
        """Efficient result processing with tensor operations"""
        scores = util.cos_sim(query_embedding, candidate_embeddings)[0].cpu().tolist()

        return [
            doc
            for doc, score in sorted(
                zip(docs, scores), key=lambda x: x[1], reverse=True
            )
            if round(score, 2) >= threshold
        ]
