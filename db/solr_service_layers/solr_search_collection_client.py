import re
from concurrent.futures import ThreadPoolExecutor

from sentence_transformers import util
from solrq import Value

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
        self._validate_search_params(query=safe_q)
        # First-stage retrieval: multi-qa-mpnet-base-dot-v1

        [docs] = self._retrieve_docs_with_knn(
            query=safe_q,
            top_k=top_k,
        )

        # Second-stage re-ranking: all-mpnet-base-v2
        reranked = self._rerank_knn_results(query=safe_q, solr_response=docs)

        search_results = []
        for item in reranked:
            if round(item[1], 2) >= threshold:
                search_results.append(item[0])

        return search_results

    def build_safe_query(self, raw_query):
        return str(Value(raw_query))

    def _validate_search_params(self, query: str) -> None:
        """Validate search parameters."""
        if not query:
            raise SolrValidationError("Query string cannot be empty")
        if self._is_malicious(query):
            raise SolrError("Cannot perform this query")

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
        self,
        query: str,
        top_k: int = -1,
        chunk_size: int = 5000,
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

        rows_count = self._get_rows_count()
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for i in range(0, rows_count, chunk_size):
                futures.append(
                    executor.submit(
                        self.fetch_results_in_chunks, i, knn_query, chunk_size
                    )
                )

            result = []
            for future in futures:
                result.append(future.result().docs)

            return result

    def fetch_results_in_chunks(self, start: int, knn_query: str, rows_count: int):
        params = {
            "q": knn_query,
            "fl": "message_id, message_content, author_id, channel_id",
            "start": start,
            "rows": rows_count,
            "cursorMark": "*",
            "sort": "score desc, message_id asc",
        }
        return self.solr_client.search(**params)

    def _rerank_knn_results(self, query: str, solr_response: dict):
        """Re-ranks KNN results using semantic similarity.
        Args:
            query: Query string
            solr_response: Solr response containing KNN results
        Returns:
            List of tuples containing re-ranked results
        """
        query_embedding = self.rerank_model.encode([query], normalize_embeddings=True)

        candidate_texts = []
        for item in solr_response:
            candidate_texts.append(item["message_content"])

        candidate_embeddings = self.rerank_model.encode(
            candidate_texts, normalize_embeddings=True
        )

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

    def _get_rows_count(self):
        rows_count_resp = make_solr_request(
            url=f"{self.cfg.BASE_URL}{self.collection_name}/select?indent=on&q=*:*&wt=json&rows=0",
            cfg=self.cfg,
            params={},
        )
        return rows_count_resp["response"]["numFound"]
