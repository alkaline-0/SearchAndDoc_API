import unittest

import pytest

from db.solr_utils.solr_admin import SolrAdminClient
from db.solr_utils.solr_exceptions import SolrConnectionError, SolrValidationError
from tests.db.mocks.mock_solr_config import MockSolrConfig


class TestSolrAdmin(unittest.TestCase):

    def setUp(self):
        # Create a mock SolrConfig object for testing
        self.mock_config = MockSolrConfig()
        self.admin_client = SolrAdminClient(cfg=self.mock_config)

    def test_connectivity_issues(self):
        """Test connectivity issues with solr."""
        with pytest.raises(SolrConnectionError) as excinfo:
            solr_admin_client = SolrAdminClient(
                cfg=MockSolrConfig(
                    BASE_URL=f"http://invalid_url:{self.mock_config.SOLR_PORT}/solr/"
                )
            )
            solr_admin_client.create_collection(collection_name="test_collection")
        assert "Failed to resolve 'invalid_url'" in str(excinfo.value)

    def test_connectivity_issues_wrong_port(self):
        """Test connectivity issues with solr."""
        with pytest.raises(SolrConnectionError) as excinfo:
            solr_admin_client = SolrAdminClient(
                cfg=MockSolrConfig(
                    BASE_URL=f"http://{self.mock_config.SOLR_HOST}:0/solr/"
                )
            )
            solr_admin_client.create_collection(collection_name="test_collection")
        assert "Failed to establish a new connection:" in str(excinfo.value)

    def test_unsuccessful_collection_creation_wrong_password(self):
        """Test unsuccessful collection creation due to wrong password."""
        with pytest.raises(SolrConnectionError) as excinfo:
            solr_admin_client = SolrAdminClient(
                cfg=MockSolrConfig(PASSWORD="wrong_password")
            )
            solr_admin_client.create_collection(collection_name="test_collection")

        assert "401 Client Error: Unauthorized for url" in str(excinfo.value)

    def test_unsuccessful_collection_creation_empty_credentials(self):
        """Test unsuccessful collection creation due to wrong password."""
        with pytest.raises(SolrValidationError) as excinfo:
            cfg = MockSolrConfig(USER_NAME="", PASSWORD=" ")
            solr_admin_client = SolrAdminClient(cfg=cfg)
            solr_admin_client.create_collection(collection_name="test_collection")

        assert "Username/password cannot be empty or whitespace-only" in str(
            excinfo.value
        )

    def test_invalid_shard_rejection(self):
        with pytest.raises(SolrValidationError) as excinfo:
            self.admin_client.create_collection(
                collection_name="test_invalid_shards", num_shards=-1
            )
        assert "Number of shards must be greater than 0" in str(excinfo.value)

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

    def test_unsuccessful_collection_creation_empty_name(self):
        """Test unsuccessful collection creation due to empty name."""
        with pytest.raises(SolrValidationError) as excinfo:
            self.admin_client.create_collection(collection_name="")
        assert "Collection name cannot be empty" in str(excinfo.value)

    def test_successful_return_collection_url_for_creating_collection_with_existing_name(
        self,
    ):
        """Test unsuccessful collection creation due to already existing collection."""
        collection_name = "test_collection"
        collection = self.admin_client.create_collection(
            collection_name=collection_name
        )

        collection_dup = self.admin_client.create_collection(
            collection_name=collection_name
        )
        assert collection == collection_dup

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

    def test_unsuccessful_deletion_of_all_collections_due_to_wrong_password(self):
        """Test unsuccessful deletion of all collections due to wrong password."""
        with pytest.raises(SolrConnectionError) as excinfo:
            collection_name = "test_collection"
            self.admin_client.create_collection(collection_name="test_collection")
            cfg = MockSolrConfig(PASSWORD="wrong_password")
            solr_admin_client = SolrAdminClient(cfg=cfg)
            solr_admin_client.delete_all_collections()
        assert "401 Client Error: Unauthorized for url" in str(excinfo.value)
        assert self.admin_client.collection_exist(collection_name) is True

    def test_successful_collection_existence_check(self):
        """Test successful collection existence check."""
        collection_name = "test_collection"
        self.admin_client.create_collection(collection_name=collection_name)

        assert self.admin_client.collection_exist(collection_name) is True

    def test_unsuccessful_collection_existence_check(self):
        """Test unsuccessful collection existence check."""

        collection_name = "non_existent_collection"

        assert self.admin_client.collection_exist(collection_name) is False

    def test_unsuccessful_collection_existence_check_due_to_wrong_password(self):
        """Test unsuccessful collection existence check due to wrong password."""
        with pytest.raises(SolrConnectionError) as excinfo:
            cfg = MockSolrConfig(PASSWORD="wrong_password")
            solr_admin_client = SolrAdminClient(cfg=cfg)
            solr_admin_client.collection_exist(collection_name="test_collection")
        assert "401 Client Error: Unauthorized for url" in str(excinfo.value)
