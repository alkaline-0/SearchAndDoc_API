import inspect
import json
from typing import Any
from urllib.parse import urljoin

import pysolr
import requests

from db.solr_utils.solr_config import SolrConfig
from db.solr_utils.solr_exceptions import (
    SolrConnectionError,
    SolrError,
    SolrValidationError,
)


class SolrAdminClient:
    def __init__(self, cfg: SolrConfig) -> None:
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
        self.cfg = cfg
        self._admin_url = urljoin(cfg.BASE_URL, "admin/collections")

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
            raise SolrValidationError("Collection name cannot be empty")

        collection_conn = urljoin(self.cfg.BASE_URL, collection_name)
        if self.collection_exist(collection_name):
            # TODO: log failure of collection creation
            return collection_conn

        params = {
            "action": "CREATE",
            "name": collection_name,
            "numShards": 1,
            "collection.configName": "solrconfig.xml",
            "user": f"{self.cfg.USER_NAME}:{self.cfg.PASSWORD}",
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
            params = {
                "action": "LIST",
                "user": f"{self.cfg.USER_NAME}:{self.cfg.PASSWORD}",
            }
            res = self._make_solr_request(params=params)

            for collection in res["collections"]:
                params = {
                    "action": "DELETE",
                    "name": collection,
                    "user": f"{self.cfg.USER_NAME}:{self.cfg.PASSWORD}",
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
        params = {
            "action": "LIST",
            "user": f"{self.cfg.USER_NAME}:{self.cfg.PASSWORD}",
        }
        res = self._make_solr_request(params=params)
        return collection_name in res["collections"]

    def create_solr_session_client(self, collection_url: str) -> pysolr.Solr:
        """Creates a Solr session client for the specified collection.

        Args:
            collection_url: URL of the Solr collection

        Returns:
            Solr session client object

        Raises:
            ValueError: If collection name is empty
        """
        if not collection_url:
            raise SolrValidationError("collection url cannot be empty")

        solr_session = pysolr.Solr(
            url=collection_url,
            timeout=10,
            auth=(self.cfg.USER_NAME, self.cfg.PASSWORD),
            always_commit=True,
        )

        return solr_session

    def _make_solr_request(self, params: dict[str, Any]) -> dict:
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

        except (
            requests.exceptions.RequestException
        ) as error:  # Catch network-related errors
            caller_frame = inspect.getouterframes(inspect.currentframe(), 2)
            print(f"Solr request failed originating from {caller_frame[1][3]}: {error}")
            raise SolrConnectionError(error)
        except json.JSONDecodeError as error:  # Catch JSON decoding errors
            print(f"Failed to decode JSON response: {error}")
            raise SolrError(error)
        except Exception as error:
            print(f"Unexpected error occurred: {error}")
            raise SolrError(error)
