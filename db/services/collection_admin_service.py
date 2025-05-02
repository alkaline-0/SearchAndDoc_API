from urllib.parse import urljoin

import requests

from db.config.solr_config import SolrConfig
from db.services.interfaces.collection_admin_service_interface import CollectionAdminServiceInterface
from db.utils.request import request


class CollectionAdminService(CollectionAdminServiceInterface):
    def __init__(self, cfg: SolrConfig) -> None:
        """Creates a new Solr Admin obj.

        Args:
            cfg: SolrConfig object containing Solr configuration

        Returns: None

        Raises:
            ValueErrorException: for any missing params
        """
        self.cfg = cfg
        self._admin_url = urljoin(cfg.BASE_URL, "admin/collections")

    def create_collection(
        self, collection_name: str, num_shards: int = 1, replica_count: int = 1
    ) -> str:
        """Creates a new Solr collection.

        Args:
            collection_name: Name of collection to create

        Returns:
            str containing the connection string to the collection

        Raises:
            requests.exceptions.HTTPError: If Solr request fails
            Exception: For other unexpected errors
        """
        collection_conn = urljoin(self.cfg.BASE_URL, collection_name)
        params = {
            "action": "CREATE",
            "name": collection_name,
            "numShards": num_shards,
            "collection.configName": "solrconfig.xml",
            "replicationFactor": replica_count,
        }
        request(params=params, url=self._admin_url, cfg=self.cfg)

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
            res = request(params=params, url=self._admin_url, cfg=self.cfg)

            for collection in res["collections"]:
                params = {
                    "action": "DELETE",
                    "name": collection,
                }
                request(params=params, url=self._admin_url, cfg=self.cfg)
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
        res = request(params=params, url=self._admin_url, cfg=self.cfg)
        return collection_name in res["collections"]
