import ray

from db.services.interfaces.indexing_data_service_interface import (
    IndexingDataServiceInterface,
)
from db.utils.encode import create_embeddings
from db.utils.interfaces.pysolr_interface import SolrClientInterface
from db.utils.interfaces.sentence_transformer_interface import (
    SentenceTransformerInterface,
)


class IndexingDataService(IndexingDataServiceInterface):
    def __init__(
        self,
        solr_client: SolrClientInterface,
        retriever_model: SentenceTransformerInterface,
    ) -> None:
        """Creates a new Solr collection agent.

        Args:
            solr_client: SolrClientInterface object for Solr operations
            retriever_model: SentenceTransformerInterface for retrieval
            rerank_model: SentenceTransformerInterface for re-ranking

        Returns: None
        """

        self.solr_client = solr_client
        self.retriever_model = retriever_model
        self.batch_size = 5000
        self.workers = 4

    def index_data(self, data: list[dict], soft_commit: bool) -> None:
        # Split data into batches upfront
        data_batches = [
            data[i : i + self.batch_size] for i in range(0, len(data), self.batch_size)
        ]

        # Parallel embedding generation
        embedding_futures = [
            create_embeddings.remote(
                [item["message_content"] for item in batch],
                self.retriever_model,
                normalize_embeddings=False,
            )
            for batch in data_batches
        ]

        # Process embeddings as they complete
        ready, not_ready = ray.wait(embedding_futures, num_returns=1)
        while ready:
            for future in ready:
                batch_idx = embedding_futures.index(future)
                self._add_bert_vector_to_data(
                    data_batches[batch_idx], ray.get(future), soft_commit=soft_commit
                )
            ready, not_ready = ray.wait(not_ready, num_returns=1)

    def _add_bert_vector_to_data(
        self, data: list[dict], embeddings, soft_commit: bool
    ) -> list[dict]:
        """Adds BERT vector to the data.

        Args:
            data: Data to add BERT vector to

        Returns:
            Data with BERT vector added

        Raises:
            ValueError: If data is empty
        """

        for i, item in enumerate(data):
            item["bert_vector"] = [float(w) for w in embeddings[i]]

        self.solr_client.add(data, softCommit=soft_commit)
