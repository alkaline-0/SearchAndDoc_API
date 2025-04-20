import inspect
import json
from urllib.parse import urljoin

import pysolr
import requests
from sentence_transformers import SentenceTransformer, util


class SolrConnectionBuilder:
    def __init__(self, user_name: str, password: str, solr_host: str, solr_port: str):
        self._user_name = user_name
        self._password = password
        self.solr_host = solr_host
        self.solr_port = solr_port

    def build_admin_connection(self) -> str:
        return urljoin(self.get_base_url(), "admin/collections")

    def get_base_url(self) -> str:
        return f"http://{self._user_name}:{self._password}@{self.solr_host}:{self.solr_port}/solr/"


class SolrAdminClient:
    def __init__(
        self,
        user_name: str,
        password: str,
        solr_host: str,
        solr_port: str,
    ) -> None:
        """Creates a new Solr Admin obj.

        Args:
            user_name: Solr user account with admin priveleges.
            password: Solr user account password.
            solr_host: host that Solr DB is running on.
            solr_port: Solr port to connect to
            collection_name: Name of collection to create.

        Returns: None

        Raises:
            ValueErrorException: for any missing params
        """

        if not all([user_name, password, solr_host, solr_port]):
            raise ValueError("All connection parameters are required")
        self._conn_builder = SolrConnectionBuilder(
            user_name=user_name,
            password=password,
            solr_host=solr_host,
            solr_port=solr_port,
        )
        self._admin_url = self._conn_builder.build_admin_connection()

    def create_collection(self, collection_name: str) -> str:
        """Creates a new Solr collection.

        Args:
            collection_name: Name of collection to create

        Returns:
            str containing the connection string to the collection

        Raises:
            requests.exceptions.HTTPError: If Solr request fails
            Exception: For other unexpected errors
        """

        if not collection_name:
            raise ValueError("Collection name cannot be empty")

        collection_conn = urljoin(self._conn_builder.build_base_url(), collection_name)
        if self.collection_exist(collection_name):
            # TODO: log failure of collection creation
            return collection_conn

        params = {
            "action": "CREATE",
            "name": collection_name,
            "numShards": 1,
            "collection.configName": "solrconfig.xml",
        }
        self._make_solr_request(params=params)
        return collection_conn

    def delete_all_collections(self) -> dict:
        """Deletes all Solr collections.
        Args:
            None
        Returns:
            Python object containing Solr response
        Raises:
            requests.exceptions.HTTPError: If Solr request fails
            Exception: For other unexpected errors
        """

        try:
            params = {"action": "LIST"}
            res = self._make_solr_request(url=self._admin_url, params=params)

            for collection in res["collections"]:
                params = {
                    "action": "DELETE",
                    "name": collection,
                }
                self._make_solr_request(params=params)
                print(f"Collection '{collection}' deleted successfully.")
        except requests.exceptions.HTTPError as error:
            print(f"Failed to delete collection: {error}")
            raise error

    def collection_exist(self, collection_name: str) -> bool:
        """Checks if a collection exists.

        Args:
            collection_name: Name of collection to check

        Returns:
            True if collection exists, False otherwise

        Raises:
            requests.exceptions.HTTPError: If Solr request fails
            Exception: For other unexpected errors
        """
        params = {"action": "LIST"}
        res = self._make_solr_request(url=self._admin_url, params=params)
        return collection_name in res["collections"]

    def _make_solr_request(self, params: dict[str]) -> dict:
        """Makes HTTP request to Solr and handles response.

        Args:
            url: Solr API endpoint URL
            params: Request parameters

        Returns:
            Python object containing parsed JSON response with the result of the request

        Raises:
            requests.exceptions.HTTPError: If request fails
            Exception: For other unexpected errors
        """
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            response = requests.get(
                self._admin_url,
                params=params,
                headers=headers,
            )
            response.raise_for_status()
            return json.loads(pysolr.force_unicode(response.content))

        except requests.exceptions.HTTPError as error:
            caller_frame = inspect.getouterframes(inspect.currentframe(), 2)
            print(f"Solr request failed originating from {caller_frame[1][3]}: {error}")
            raise
        except Exception as error:
            print(f"Unexpected error occurred: {error}")
            raise


class SolrCollectionClient:
    def __init__(
        self,
        collection_conn: str,
        collection_name: str,
        retriever_model="sentence-transformers/multi-qa-mpnet-base-dot-v1",
        rerank_model="sentence-transformers/all-mpnet-base-v2",
    ) -> None:
        """Creates a new Solr collection agent.
        Args:
            collection_conn: Solr connection string.
            collection_name: Name of Solr collection.
        Returns: None
        Raises:
            ValueErrorException: for any missing params
        """

        if not all([collection_conn, collection_name]):
            raise ValueError("All connection parameters are required")

        self._conn_url = collection_conn
        self._pysolr_obj = pysolr.Solr(self._conn_url)
        self.rerank_model = SentenceTransformer(rerank_model)
        self.retriever_model = SentenceTransformer(retriever_model)

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
            raise ValueError("Data to index cannot be empty")

        for item in data:
            content = item["message_content"]
            embedding = self.retriever_model.encode([content])
            item["bert_vector"] = [float(w) for w in embedding[0]]

        self._pysolr_obj.add(data)

        self._pysolr_obj.commit(softCommit=soft_commit)

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
        if not q:
            raise ValueError("Query string cannot be empty")
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

    def _retrieve_docs_with_knn(
        self, begin_row: int, end_row: int, query: str
    ) -> pysolr.Results:
        """Retrieves documents from Solr using KNN search.
        Args:
            begin_row: Starting row for pagination
            end_row: Ending row for pagination
            query: Query string
        Returns:
            Dictionary containing Solr response
        """

        retriever_embedding = self.retriever_model.encode([query])
        knn_query = "{!knn f=bert_vector}" + str(
            [float(w) for w in retriever_embedding[0]]
        )

        return self._pysolr_obj.search(
            fl=["message_id", "message_content"],
            q=knn_query,
            start=begin_row,
            rows=end_row,
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


class SolrClientFactory:
    @staticmethod
    def create(
        user_name: str,
        password: str,
        solr_host: str,
        solr_port: str,
        collection_name: str,
    ) -> SolrCollectionClient:
        """Creates a SolrCollectionAgent instance.
        Args:
            user_name: Solr user account with admin privileges.
            password: Solr user account password.
            solr_host: host that Solr DB is running on.
            solr_port: Solr port to connect to
            collection_name: Name of collection to create.
        Returns:
            SolrCollectionAgent instance
        """
        admin = SolrAdminClient(
            user_name=user_name,
            password=password,
            solr_host=solr_host,
            solr_port=solr_port,
        )

        collection_conn = admin.create_collection(collection_name=collection_name)
        return SolrCollectionClient(collection_conn, collection_name)

    @staticmethod
    def delete_all_collections(
        user_name: str,
        password: str,
        solr_host: str,
        solr_port: str,
    ) -> None:
        """Deletes all Solr collections.
        Args:
            user_name: Solr user account with admin privileges.
            password: Solr user account password.
            solr_host: host that Solr DB is running on.
            solr_port: Solr port to connect to
        Returns:
            None
        """
        admin = SolrAdminClient(
            user_name=user_name,
            password=password,
            solr_host=solr_host,
            solr_port=solr_port,
        )
        admin.delete_all_collections()
