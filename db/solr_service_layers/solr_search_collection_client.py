import re

from sentence_transformers import util
from solrq import Value

from db.helpers.interfaces.sentence_transformer_interface import (
    SentenceTransformerInterface,
)
from db.solr_utils.interfaces.pysolr_interface import SolrClientInterface
from db.solr_utils.solr_exceptions import SolrError, SolrValidationError


class SolrSearchCollectionClient:
    def __init__(
        self,
        solr_client: SolrClientInterface,
        retriever_model: SentenceTransformerInterface,
        rerank_model: SentenceTransformerInterface,
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

    def semantic_search(
        self,
        q: str,
        row_begin: int,
        row_end: int,
        threshold: float = 0.2,
        top_k: int = -1,
    ) -> list[dict]:
        """Performs semantic search on the Solr collection.
        Args:
            q: Query string
            row_begin: Starting row for pagination
            row_end: Ending row for pagination
            threshold: Minimum score threshold for results
        Returns:
            List of dictionaries containing search results
        Raises:
            SolrValidationError: If validation fails
        """
        safe_q = self.build_safe_query(raw_query=q)
        self._validate_search_params(query=safe_q, row_begin=row_begin, row_end=row_end)
        # First-stage retrieval: multi-qa-mpnet-base-dot-v1
        solr_response = self._retrieve_docs_with_knn(
            row_begin=row_begin, row_end=row_end, query=safe_q, top_k=top_k
        )

        # Second-stage re-ranking: all-mpnet-base-v2
        reranked = self._rerank_knn_results(query=safe_q, solr_response=solr_response)

        search_results = []
        for text, score, msg_id in reranked:
            if round(score, 2) >= threshold:
                search_results.append(
                    {"message_id": msg_id, "score": score, "message_content": text}
                )

        return search_results

    def build_safe_query(self, raw_query):
        return str(Value(raw_query))

    def _validate_search_params(self, query: str, row_begin: int, row_end: int) -> None:
        """Validate search parameters."""
        if not query:
            raise SolrValidationError("Query string cannot be empty")
        if self._is_malicious(query):
            raise SolrError("Cannot perform this query")
        if row_begin < 0:
            raise SolrValidationError("Row begin must be non-negative")
        if row_end <= row_begin:
            raise SolrValidationError("Row end must be greater than row begin")

    def _is_malicious(self, query: str):
        patterns = [
            r"drop\s",  # Catches "DROP TABLE", "DROP COLLECTION"
            r"delete\s",
            r";\s*--",  # SQL-style comments
            r"\b(shutdown|truncate)\b",
            r"(?i)(drop|delete|alter)",  # Case-insensitive
        ]
        return any(re.search(pattern, query, re.IGNORECASE) for pattern in patterns)

    def _retrieve_docs_with_knn(
        self, row_begin: int, row_end: int, query: str, top_k: int = -1
    ) -> dict:
        """Retrieves documents from Solr using KNN search.
        Args:
            row_begin: Starting row for pagination
            row_end: Ending row for pagination
            query: Query string
            top_k: Number of top K results to retrieve
        Returns:
            Dictionary containing Solr response
        """

        retriever_embedding = self.retriever_model.encode([query])
        if top_k > 0:
            knn_query = f"{{!knn f=bert_vector topK={top_k}}}{[float(w) for w in retriever_embedding[0]]}"
        else:
            knn_query = (
                f"{{!knn f=bert_vector }}{[float(w) for w in retriever_embedding[0]]}"
            )

        return self.solr_client.search(
            fl=["message_id", "message_content"],
            q=knn_query,
            qt="/export",
            start=row_begin,
            rows=row_end - row_begin,
            sort="score desc",
        )

    def _rerank_knn_results(self, query: str, solr_response: dict):
        """Re-ranks KNN results using semantic similarity.
        Args:
            query: Query string
            solr_response: Solr response containing KNN results
        Returns:
            List of tuples containing re-ranked results
        """
        query_embedding = self.rerank_model.encode([query], normalize_embeddings=True)
        candidate_texts = [(item["message_content"]) for item in solr_response.docs]
        candidate_embeddings = self.rerank_model.encode(
            candidate_texts, normalize_embeddings=True
        )

        # Cosine similarity between query and each candidate
        scores = util.cos_sim(query_embedding, candidate_embeddings)[0].cpu().tolist()

        # Zip together for sorting
        return sorted(
            zip(
                candidate_texts,
                scores,
                [(item["message_id"]) for item in solr_response.docs],
            ),
            key=lambda x: x[1],
            reverse=True,
        )
