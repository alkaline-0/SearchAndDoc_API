import re

from sentence_transformers import util
from solrq import Value

from db.solr_utils.interfaces.pysolr_interface import SolrClientInterface
from db.helpers.interfaces.sentence_transformer_interface import SentenceTransformerInterface
from db.solr_utils.solr_exceptions import SolrError, SolrValidationError


class SolrIndexCollectionClient:
    def __init__(
        self,
        solr_client: SolrClientInterface,
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

    def index_data(self, data: list[dict], soft_commit: bool) -> None:
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

