import json
from typing import Any, Dict

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
        """
        self._user_name = user_name
        self._password = password
        self._construct_url(solr_host=solr_host, solr_port=solr_port)
        self._pysolr_obj = pysolr.Solr(self._conn_url, always_commit=True)
        self._instance_dir = "/opt/solr-8.11.1/server/solr"
        self._config_name = "solrconfig.xml"
        self._schema_name = "managed-schema.xml"

    def create_collection(self, collection_name: str) -> dict[str, Any] | None:
        """Creates a new Solr collection.

        Args:
            collection_name: Name of collection to create

        Returns:
            Dict containing Solr response on success, None if collection exists

        Raises:
            requests.exceptions.HTTPError: If Solr request fails
            Exception: For other unexpected errors
        """
        if self._collection_exist(collection_name):
            return None

        params = {
            "action": "CREATE",
            "name": collection_name,
            "numShards": 1,
            "collection.configName": self._config_name,
        }
        return self._make_solr_request(url=self._admin_url, params=params)

    def create_new_core(
        self, discord_server_id: str, collection_name: str = "vault"
    ) -> Dict[str, Any]:
        """Creates a new Solr core.

        Args:
            discord_server_id: Discord server ID to use as core name
            collection_name: Name of collection to associate with core

        Returns:
            Dict containing Solr response

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

    def _collection_exist(self, collection_name: str) -> bool:
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

    def _make_solr_request(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Makes HTTP request to Solr and handles response.

        Args:
            url: Solr API endpoint URL
            params: Request parameters

        Returns:
            Dict containing parsed JSON response

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
            print(f"Solr request failed originating from {params['action']}: {error}")
            raise
        except Exception as error:
            print(f"Unexpected error occurred: {error}")
            raise
