import inspect
import json
from typing import Any

import pysolr
import requests

"""Solr configuration settings."""

from dataclasses import dataclass


@dataclass
class SolrConfig:
    """Solr configuration parameters."""

    INSTANCE_DIR: str = "/opt/solr-8.11.1/server/solr"
    CONFIG_NAME: str = "solrconfig.xml"
    SCHEMA_NAME: str = "managed-schema.xml"
    NUM_SHARDS: int = 1


class Solr:
    """Client for interacting with Solr search engine.

    Handles core and collection management operations against a Solr instance.

    Attributes:
        _admin_url: URL for Solr admin API
        _user_name: Solr authentication username
        _password: Solr authentication password
        _conn_url: Base connection URL
        _collection_conn_url: URL for collection operations
        _config_name: Name of Solr config file
        _instance_dir: Solr instance directory path
        _schema_name: Name of schema file
    """

    def __init__(
        self, user_name: str, password: str, solr_host: str, solr_port: str
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
        if not all([user_name, password, solr_host, solr_port]):
            raise ValueError("All connection parameters are required")
        self._user_name = user_name
        self._password = password
        self._construct_url(solr_host=solr_host, solr_port=solr_port)
        self._config_name = SolrConfig.CONFIG_NAME
        self._instance_dir = SolrConfig.INSTANCE_DIR
        self._schema_name = SolrConfig.SCHEMA_NAME

    def create_collection(self, collection_name: str) -> Any:
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
            "collection.configName": self._config_name,
        }
        return self._make_solr_request(url=self._collection_conn_url, params=params)

    def create_new_core(
        self, discord_server_id: str, collection_name: str = "vault"
    ) -> Any:
        """Creates a new Solr core.

        Args:
            discord_server_id: Discord server ID to use as core name
            collection_name: Name of collection to associate with core

        Returns:
            Python object with Solr response on success, None if core exists

        Raises:
            requests.exceptions.HTTPError: If Solr request fails
            Exception: For other unexpected errors
        """
        if not discord_server_id:
            raise ValueError("Discord server ID cannot be empty")
        params = {
            "action": "CREATE",
            "name": discord_server_id,
            "config": self._config_name,
            "instance_dir": self._instance_dir,
            "schema": self._schema_name,
            "collection": collection_name,
        }
        return self._make_solr_request(url=self._admin_url, params=params)

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
        res = self._make_solr_request(url=self._collection_conn_url, params=params)
        return collection_name in res["collections"]

    def index_data(self, data: list[dict], core_name: str) -> Any:
        """Indexes data into a Solr core.

        Args:
            data: Data to index
            core_name: Name of Solr core

        Returns:
            Python object with Solr response

        Raises:
            requests.exceptions.HTTPError: If Solr request fails
            Exception: For other unexpected errors
        """
        self._validate_index_params(data, core_name)

        core_url = self._conn_url + "/" + core_name
        pysolr_obj = pysolr.Solr(core_url)
        try:
            pysolr_obj.add(data, softCommit=True)
        except requests.exceptions.HTTPError as error:
            print(f"Failed to index data in Solr core '{core_name}': {error}")
            raise error

    def index_data_with_hard_commit(self, data: list[dict], core_name: str) -> Any:
        """Indexes data into a Solr core with hard commit.
        Args:
            data: Data to index
            core_name: Name of Solr core
        Returns:
            Python object with Solr response
        Raises:
            requests.exceptions.HTTPError: If Solr request fails
            Exception: For other unexpected errors
        """
        self._validate_index_params(data, core_name)
        core_url = self._conn_url + "/" + core_name
        pysolr_obj = pysolr.Solr(core_url, always_commit=True)
        try:
            pysolr_obj.add(data, commit=True)
        except requests.exceptions.HTTPError as error:
            print(f"Failed to index data in Solr core '{core_name}': {error}")
            raise error

    def core_exist(self, core_name: str) -> bool:
        """Checks if a Solr core exists.

        Args:
            core_name: Name of core to check

        Returns:
            True if core exists, False otherwise

        Raises:
            requests.exceptions.HTTPError: If Solr request fails
            Exception: For other unexpected errors
        """
        if not core_name:
            raise ValueError("Core name cannot be empty")

        params = {"action": "STATUS", core_name: core_name}
        res = self._make_solr_request(url=self._admin_url, params=params)
        return core_name in res["status"]

    def delete_all_collections(self) -> None:
        try:
            params = {"action": "LIST"}
            res = self._make_solr_request(url=self._collection_conn_url, params=params)

            for collection in res["collections"]:
                params = {
                    "action": "DELETE",
                    "name": collection,
                }
                self._make_solr_request(url=self._collection_conn_url, params=params)
                print(f"Collection '{collection}' deleted successfully.")
        except requests.exceptions.HTTPError as error:
            print(f"Failed to delete collection: {error}")
            raise error

    def select_docs(self, query: str, core_name: str) -> Any:
        """Selects documents from a Solr core based on a query.

        Args:
            query: Query string to filter documents
            core_name: Name of Solr core

        Returns:
            Python object with Solr response

        Raises:
            requests.exceptions.HTTPError: If Solr request fails
            Exception: For other unexpected errors
        """
        if not core_name:
            raise ValueError("Core name cannot be empty")
        if not query:
            raise ValueError("Query cannot be empty")
        if not self.core_exist(core_name):
            raise ValueError("Core does not exist")
        try:
            core_url = f"{self._conn_url}/{core_name}/select"
            params = {"q": query}
            response = self._make_solr_request(url=core_url, params=params)

            return response
        except requests.exceptions.HTTPError as error:
            print(f"Failed to select documents from Solr core '{core_name}': {error}")
            raise error

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

    def _construct_url(self, solr_host: str, solr_port: str) -> None:
        """Constructs Solr URLs from connection details.

        Args:
            solr_host: Solr host address
            solr_port: Solr port number
        """
        self._conn_url = (
            f"http://{self._user_name}:{self._password}@{solr_host}:{solr_port}/solr"
        )
        self._admin_url = f"{self._conn_url}/admin/cores"
        self._collection_conn_url = f"{self._conn_url}/admin/collections"

    def _validate_index_params(
        self, data: list[dict[str, any]], core_name: str
    ) -> None:
        """Validate indexing parameters.

        Args:
            data: Data to index
            core_name: Name of Solr core

        Raises:
            SolrValidationError: If parameters are invalid
        """
        if not core_name:
            raise ValueError("Core name cannot be empty")
        if not data:
            raise ValueError("Data to index cannot be empty")
        if not self.core_exist(core_name):
            raise ValueError("Core does not exist")
