import inspect
import json
from typing import Any

import pysolr
import requests


class Solr:
    """Client for interacting with Solr search engine.

    Handles core and collection management operations against a Solr instance.

    Attributes:
        _pysolr_obj: PySolr client instance
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
        self._pysolr_obj = pysolr.Solr(self._conn_url, always_commit=True)
        self._instance_dir = "/opt/solr-8.11.1/server/solr"
        self._config_name = "solrconfig.xml"
        self._schema_name = "managed-schema.xml"

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
        params = {
            "action": "CREATE",
            "name": discord_server_id,
            "config": self._config_name,
            "instance_dir": self._instance_dir,
            "schema": self._schema_name,
            "collection": collection_name,
        }
        return self._make_solr_request(url=self._admin_url, params=params)

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
