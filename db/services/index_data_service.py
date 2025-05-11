from logging import Logger

import ray

from db.data_access.interfaces.pysolr_interface import SolrClientInterface
from db.services.interfaces.index_data_service_interface import (
    IndexDataServiceInterface,
)
from db.utils.encode import create_embeddings
from db.utils.interfaces.sentence_transformer_interface import (
    SentenceTransformerInterface,
)


class IndexDataService(IndexDataServiceInterface):
    def __init__(
        self,
        logger: Logger,
        solr_client: SolrClientInterface,
        retriever_model: SentenceTransformerInterface,
    ) -> None:
        """Creates a new indexing data collection agent.

        Args:
            solr_client: SolrClientInterface object for Solr operations
            retriever_model: SentenceTransformerInterface for retrieval

        Returns: None
        """

        self.solr_client = solr_client
        self.retriever_model = retriever_model
        self.batch_size = 5000
        self.workers = 4
        self._logger = logger

    def index_data(self, data: list[dict], soft_commit: bool) -> None:
        data_batches = [
            data[i : i + self.batch_size] for i in range(0, len(data), self.batch_size)
        ]

        embedding_futures = [
            create_embeddings.remote(
                [item["message_content"] for item in batch],
                self.retriever_model,
                normalize_embeddings=False,
            )
            for batch in data_batches
        ]

        ready, not_ready = ray.wait(embedding_futures, num_returns=1)
        while ready:
            for future in ready:
                batch_idx = embedding_futures.index(future)
                self._logger.info(f"starting processing batch {batch_idx}.")
                self._add_bert_vector_to_data(
                    data_batches[batch_idx], ray.get(future), soft_commit=soft_commit
                )
                self._logger.info(f"Indexed batch {batch_idx}.")
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

        self.solr_client.add(data, soft_commit=soft_commit)
