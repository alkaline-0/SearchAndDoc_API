import unittest
from unittest.mock import patch

from db.services.collection_admin_service import CollectionAdminService
from tests.db.mocks.mock_solr_config import MockSolrConfig
from utils.get_logger import get_logger


class TestCollectionAdmin(unittest.TestCase):

    def setUp(self):
        # Create a mock SolrConfig object for testing
        self.mock_config = MockSolrConfig()
        self.admin_client = CollectionAdminService(
            cfg=self.mock_config, logger=get_logger()
        )

    def test_successful_collection_creation_2_shards_2_replicas(self):
        """Test successful collection creation."""
        with patch.object(self.admin_client, "_logger") as mock_logger:
            collection_name = "test_collection_2_shards_2_replicas"
            num_shards = 2
            replicas = 2
            collection_url = self.admin_client.create_collection(
                collection_name=collection_name,
                num_shards=num_shards,
                replica_count=replicas,
            )

            mock_logger.info.assert_called_with(
                f"Creating a new collection with the name {collection_name}, {num_shards} shards and {replicas} replicas."
            )
        assert (
            collection_url
            == f"http://{self.mock_config.SOLR_HOST}:{self.mock_config.SOLR_PORT}/solr/{collection_name}"
        )

    def test_successful_delete_all_collections(self):
        """Test successful deletion of all collections."""
        collection_name = "test_collection"
        self.admin_client.create_collection(collection_name=collection_name)
        with patch.object(self.admin_client, "_logger") as mock_logger:
            self.admin_client.delete_all_collections()

        mock_logger.info.assert_called_with(
            f"Collection '{collection_name}' deleted successfully."
        )
        assert self.admin_client.collection_exist(collection_name) is False

    def test_repeated_deletions(self):
        with patch.object(self.admin_client, "_logger"):
            self.admin_client.delete_all_collections()
            self.admin_client.delete_all_collections()  # Should not error
        assert True  # Test passes if no exception

    def test_return_true_for_existing_collection_check(self):
        """Test successful collection existence check."""
        collection_name = "test_collection"
        self.admin_client.create_collection(collection_name=collection_name)
        with patch.object(self.admin_client, "_logger") as mock_logger:
            res = self.admin_client.collection_exist(collection_name)

        assert res is True
        mock_logger.info.assert_called_with(f"Checking if '{collection_name}' exists.")

    def test_return_false_for_none_existing_collection_check(self):
        """Test unsuccessful collection existence check."""
        with patch.object(self.admin_client, "_logger"):

            collection_name = "non_existent_collection"

        assert self.admin_client.collection_exist(collection_name) is False
