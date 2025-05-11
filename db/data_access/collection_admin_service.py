from logging import Logger
from urllib.parse import urljoin

from db.config.solr_config import SolrConfig
from db.data_access.interfaces.collection_admin_service_interface import (
    CollectionAdminServiceInterface,
)
from db.data_access.request import request


class CollectionAdminService(CollectionAdminServiceInterface):
    def __init__(self, cfg: SolrConfig, logger: Logger = None) -> None:
        """Creates a new Solr Admin obj.

        Args:
            cfg: SolrConfig object containing Solr configuration
            logger: Logger object

        Returns: None
        """
        self.cfg = cfg
        self._admin_url = urljoin(cfg.BASE_URL, "admin/collections")
        self._logger = logger

    def create_collection(
        self, collection_name: str, num_shards: int = 1, replica_count: int = 1
    ) -> str:
        """Creates a new Solr collection.

        Args:
            collection_name: Name of collection to create
            num_shards: Number of shards to create replicas with minimum is 1
            replicas_count: Number of replicas of the collection, minimum is 1

        Returns:
            str containing the connection string to the collection
        """
        collection_conn = urljoin(self.cfg.BASE_URL, collection_name)
        params = {
            "action": "CREATE",
            "name": collection_name,
            "numShards": num_shards,
            "collection.configName": "solrconfig.xml",
            "replicationFactor": replica_count,
        }

        self._logger.info(
            f"Creating a new collection with the name {collection_name}, {num_shards} shards and {replica_count} replicas."
        )

        request(params=params, url=self._admin_url, cfg=self.cfg, logger=self._logger)

        return collection_conn

    def delete_all_collections(self) -> None:
        """Deletes all Solr collections.

        Args:
            None

        Returns:
            Python object containing Solr response

        Raises:
            requests.exceptions.HTTPError: If Solr request fails
            Exception: For other unexpected errors
        """

        params = {
            "action": "LIST",
        }
        res = request(
            params=params, url=self._admin_url, cfg=self.cfg, logger=self._logger
        )

        for collection in res["collections"]:
            params = {
                "action": "DELETE",
                "name": collection,
            }
            request(
                params=params,
                url=self._admin_url,
                cfg=self.cfg,
                logger=self._logger,
            )
            self._logger.info(f"Collection '{collection}' deleted successfully.")

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
        self._logger.info(f"Checking if '{collection_name}' exists.")
        res = request(
            params=params, url=self._admin_url, cfg=self.cfg, logger=self._logger
        )
        return collection_name in res["collections"]

    def get_collection_url(self, collection_name: str):
        return urljoin(self.cfg.BASE_URL, collection_name)
