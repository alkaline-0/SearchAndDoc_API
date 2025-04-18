import inspect
import json
from typing import Any
from urllib.parse import urljoin

import pysolr
import requests
from sentence_transformers import SentenceTransformer

"""Solr configuration settings."""


class SolrCollectionAgent:
    def __init__(
        self,
        user_name: str,
        password: str,
        solr_host: str,
        solr_port: str,
        collection_name: str,
    ) -> None:
        """Initializes the Solr client with connection details.

        Args:
            user_name: Authentication username
            password: Authentication password
            solr_host: Solr host address
            solr_port: Solr port number

        Raises:
            ValueError: If any required params are empty
            ConnectionError: If unable to connect to Solr
        """
        if not all([user_name, password, solr_host, solr_port, collection_name]):
            raise ValueError("All connection parameters are required")
        self._user_name = user_name
        self._password = password
        self.collection_name = collection_name
        base_url = (
            f"http://{self._user_name}:{self._password}@{solr_host}:{solr_port}/solr/"
        )
        self._admin_url = urljoin(base_url + "/", "admin/collections")
        self._create_collection(collection_name)
        self._conn_url = urljoin(base_url, collection_name)
        self._pysolr_obj = pysolr.Solr(self._conn_url)
        self.model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

    def _create_collection(self, collection_name: str) -> Any:
        """Creates a new Solr collection.

        Args:
            collection_name: Name of collection to create

        Returns:
            Python object containing Solr response on success, None if collection exists

        Raises:
            requests.exceptions.HTTPError: If Solr request fails
            Exception: For other unexpected errors
        """

        if not collection_name:
            raise ValueError("Collection name cannot be empty")

        if self.collection_exist(collection_name):
            # TODO: log failure of collection creation
            return None

        params = {
            "action": "CREATE",
            "name": collection_name,
            "numShards": 1,
            "collection.configName": "solrconfig.xml",
        }
        return self._make_solr_request(url=self._admin_url, params=params)

    def delete_all_collections(self) -> None:
        try:
            params = {"action": "LIST"}
            res = self._make_solr_request(url=self._admin_url, params=params)

            for collection in res["collections"]:
                params = {
                    "action": "DELETE",
                    "name": collection,
                }
                self._make_solr_request(url=self._admin_url, params=params)
                print(f"Collection '{collection}' deleted successfully.")
        except requests.exceptions.HTTPError as error:
            print(f"Failed to delete collection: {error}")
            raise error

    def select_docs(self, query: str) -> Any:
        """Selects documents from a Solr collection based on a query.

        Args:
            query: Query string to filter documents
            collection_name: Name of Solr collection

        Returns:
            Python object with Solr response

        Raises:
            requests.exceptions.HTTPError: If Solr request fails
            Exception: For other unexpected errors
        """
        if not query:
            raise ValueError("Query cannot be empty")
        try:
            response = self._pysolr_obj.search(query)

            return response
        except requests.exceptions.HTTPError as error:
            print(
                f"Failed to select documents from Solr collection '{self.collection_name}': {error}"
            )
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

    def index_data(self, data: list[dict], soft_commit: bool) -> Any:
        """Indexes data into a Solr collection.

        Args:
            data: Data to index
            collection_name: Name of Solr collection

        Returns:
            Python object with Solr response

        Raises:
            requests.exceptions.HTTPError: If Solr request fails
            Exception: For other unexpected errors
        """
        # if not data:
        #     raise ValueError("Data to index cannot be empty")
        # try:
        #     if soft_commit:
        #         self._pysolr_obj.add(data, softCommit=True)
        #     else:
        #         self._pysolr_obj.add(data, commit=True)
        # except requests.exceptions.HTTPError as error:
        #     print(
        #         f"Failed to index data in Solr collection '{self.collection_name}': {error}"
        #     )
        #     raise error
        self._pysolr_obj.add(data)
        self._pysolr_obj.commit()

    def update_dense_index(self):
        # retrieve all the recrods from collection
        solr_response = self._pysolr_obj.search(
            q="*:*",
            rows=2147483647,
            start=0,
            fl="message_id,message_content",
            wt="json",
        )

        # Save topic info alongside each document (store in Solr or side index)
        for item in solr_response:
            content = item["message_content"]
            idx = item["message_id"]
            embedding = self.model.encode([content])
            self._pysolr_obj.add(
                {
                    "message_id": idx,
                    "bert_vector": {"set": [float(w) for w in embedding[0]]},
                },
            )
            self._pysolr_obj.commit()

    def semantic_search(self, query):
        print(f"************ Semantic search for {query}")
        embedding = self.model.encode([query])
        # print({str([float(w) for w in embedding[0]])})

        # Search in Solr via vector search
        q = "{!knn f=bert_vector topK=50}" + str([float(w) for w in embedding[0]])
        solr_response = self._pysolr_obj.search(
            fl=["message_id", "message_content", "score"], q=q, rows=2147483647
        )

        for item in solr_response.docs:
            print(
                item["message_content"],
                "\nscore : ",
                item["score"],
            )

    def _make_solr_request(self, url: str, params: dict[str]) -> Any:
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
                url, data=pysolr.safe_urlencode(params), headers=headers
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
