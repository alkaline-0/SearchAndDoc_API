from sentence_transformers import util

from db.solr_utils.pysolr_interface import SolrClientInterface
from db.solr_utils.sentence_transformer_interface import SentenceTransformerInterface
from db.solr_utils.solr_exceptions import SolrValidationError


class SolrCollectionClient:
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

    def index_data(self, data: list[dict], soft_commit: bool) -> str:
        """Indexes data into a Solr collection.

        Args:
            data: Data to index
            soft_commit: Whether to perform a soft commit

        Returns:
            Str containing the response from Solr

        Raises:
            requests.exceptions.HTTPError: If Solr request fails
            Exception: For other unexpected errors
            ValueError: If data is empty
        """
        if not data:
            raise SolrValidationError("Data to index cannot be empty")

        contents = [item["message_content"] for item in data]
        embeddings = self.retriever_model.encode(contents)  # Batch encode

        for i, item in enumerate(data):
            item["bert_vector"] = [float(w) for w in embeddings[i]]

        self.solr_client.add(data)
        self.solr_client.commit(softCommit=soft_commit)

    def semantic_search(
        self, q: str, row_begin: int, row_end: int, threshold: float = 0.2
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
            ValueError: If query is empty
        """
        self._validate_search_params(query=q, row_begin=row_begin, row_end=row_end)
        # First-stage retrieval: multi-qa-mpnet-base-dot-v1
        solr_response = self._retrieve_docs_with_knn(
            row_begin=row_begin, row_end=row_end, query=q
        )

        # Second-stage re-ranking: all-mpnet-base-v2
        reranked = self._rerank_knn_results(query=q, solr_response=solr_response)

        search_results = []
        for text, score, msg_id in reranked:
            if round(score, 4) >= threshold:
                search_results.append(
                    {"message_id": msg_id, "score": score, "message_content": text}
                )

        return search_results

    def _validate_search_params(self, query: str, row_begin: int, row_end: int) -> None:
        """Validate search parameters."""
        if not query:
            raise SolrValidationError("Query string cannot be empty")
        if row_begin < 0:
            raise SolrValidationError("Row begin must be non-negative")
        if row_end <= row_begin:
            raise SolrValidationError("Row end must be greater than row begin")

    def _retrieve_docs_with_knn(self, row_begin: int, row_end: int, query: str) -> dict:
        """Retrieves documents from Solr using KNN search.
        Args:
            row_begin: Starting row for pagination
            row_end: Ending row for pagination
            query: Query string
        Returns:
            Dictionary containing Solr response
        """

        retriever_embedding = self.retriever_model.encode([query])
        knn_query = f"{{!knn f=bert_vector topK=100}}{[float(w) for w in retriever_embedding[0]]}"

        return self.solr_client.search(
            fl=["message_id", "message_content"],
            q=knn_query,
            start=row_begin,
            rows=row_end - row_begin,
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
