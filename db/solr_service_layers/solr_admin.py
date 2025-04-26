from urllib.parse import urljoin

import requests

from db.helpers.solr_request import make_solr_request
from db.solr_utils.solr_config import SolrConfig
from db.solr_utils.solr_exceptions import SolrConnectionError, SolrValidationError


class SolrAdminClient:
    def __init__(self, cfg: SolrConfig) -> None:
        """Creates a new Solr Admin obj.

        Args:
            cfg: SolrConfig object containing Solr configuration

        Returns: None

        Raises:
            ValueErrorException: for any missing params
        """

        self._validate_credentials(cfg)

        self.cfg = cfg
        self._admin_url = urljoin(cfg.BASE_URL, "admin/collections")

    def _validate_credentials(self, cfg):
        """Handles None, empty strings, and whitespace."""
        if cfg.USER_NAME is None or cfg.PASSWORD is None:
            raise SolrValidationError("Username/password cannot be None")

        if not cfg.USER_NAME.strip() or not cfg.PASSWORD.strip():
            raise SolrValidationError(
                "Username/password cannot be empty or whitespace-only"
            )

    def create_collection(self, collection_name: str, num_shards: int = 1) -> str:
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
        if num_shards <= 0:
            raise SolrValidationError("Number of shards must be greater than 0")

        collection_conn = urljoin(self.cfg.BASE_URL, collection_name)
        if self.collection_exist(collection_name):
            # TODO: log failure of collection creation
            return collection_conn

        params = {
            "action": "CREATE",
            "name": collection_name,
            "numShards": num_shards,
            "collection.configName": "solrconfig.xml",
        }
        try:
            make_solr_request(params=params, url=self._admin_url, cfg=self.cfg)
        except SolrConnectionError:
            raise SolrConnectionError()
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
            }
            res = make_solr_request(params=params, url=self.admin_url, cfg=self.cfg)

            for collection in res["collections"]:
                params = {
                    "action": "DELETE",
                    "name": collection,
                }
                make_solr_request(params=params, url=self.admin_url, cfg=self.cfg)
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
        }
        res = make_solr_request(params=params, url=self._admin_url, cfg=self.cfg)
        return collection_name in res["collections"]
