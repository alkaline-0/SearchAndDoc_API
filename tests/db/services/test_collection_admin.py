import unittest

import pytest

from db.services.admin import CollectionAdmin
from db.utils.exceptions import SolrConnectionError
from tests.db.mocks.mock_solr_config import MockSolrConfig


class TestCollectionAdmin(unittest.TestCase):

    def setUp(self):
        # Create a mock SolrConfig object for testing
        self.mock_config = MockSolrConfig()
        self.admin_client = CollectionAdmin(cfg=self.mock_config)

    def test_connectivity_issues(self):
        """Test connectivity issues with solr."""
        with pytest.raises(SolrConnectionError) as excinfo:
            solr_admin_client = CollectionAdmin(
                cfg=MockSolrConfig(
                    BASE_URL=f"http://invalid_url:{self.mock_config.SOLR_PORT}/solr/"
                )
            )
            solr_admin_client.create_collection(collection_name="test_collection")
        assert "Failed to resolve 'invalid_url'" in str(excinfo.value)

    def test_connectivity_issues_wrong_port(self):
        """Test connectivity issues with solr."""
        with pytest.raises(SolrConnectionError) as excinfo:
            solr_admin_client = CollectionAdmin(
                cfg=MockSolrConfig(
                    BASE_URL=f"http://{self.mock_config.SOLR_HOST}:0/solr/"
                )
            )
            solr_admin_client.create_collection(collection_name="test_collection")
        assert "Failed to establish a new connection:" in str(excinfo.value)

    def test_successful_collection_creation_2_shards(self):
        """Test successful collection creation."""
        collection_name = "test_collection_2_shards"
        num_shards = 2
        collection_url = self.admin_client.create_collection(
            collection_name=collection_name, num_shards=num_shards
        )

        assert (
            collection_url
            == f"http://{self.mock_config.SOLR_HOST}:{self.mock_config.SOLR_PORT}/solr/{collection_name}"
        )

    def test_successful_collection_creation(self):
        """Test successful collection creation."""
        collection_name = "test_collection"
        collection_url = self.admin_client.create_collection(
            collection_name=collection_name
        )

        assert (
            collection_url
            == f"http://{self.mock_config.SOLR_HOST}:{self.mock_config.SOLR_PORT}/solr/{collection_name}"
        )
        assert self.admin_client.collection_exist(collection_name) is True

    def test_successful_delete_all_collections(self):
        """Test successful deletion of all collections."""
        collection_name = "test_collection"
        self.admin_client.create_collection(collection_name=collection_name)
        self.admin_client.delete_all_collections()

        assert self.admin_client.collection_exist(collection_name) is False

    def test_repeated_deletions(self):
        self.admin_client.delete_all_collections()
        self.admin_client.delete_all_collections()  # Should not error
        assert True  # Test passes if no exception

    def test_successful_collection_existence_check(self):
        """Test successful collection existence check."""
        collection_name = "test_collection"
        self.admin_client.create_collection(collection_name=collection_name)

        assert self.admin_client.collection_exist(collection_name) is True

    def test_unsuccessful_collection_existence_check(self):
        """Test unsuccessful collection existence check."""

        collection_name = "non_existent_collection"

        assert self.admin_client.collection_exist(collection_name) is False
