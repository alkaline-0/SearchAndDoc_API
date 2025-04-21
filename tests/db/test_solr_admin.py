import pytest

from db.solr_utils.solr_admin import SolrAdminClient
from db.solr_utils.solr_exceptions import SolrConnectionError, SolrValidationError
from tests.db.mocks.mock_solr_config import MockSolrConfig


class TestSolrAdmin:

    def test_unsuccessful_collection_creation_wrong_password(self):
        """Test unsuccessful collection creation due to wrong password."""
        with pytest.raises(SolrConnectionError) as excinfo:
            solr_admin_client = SolrAdminClient(
                cfg=MockSolrConfig(PASSWORD="wrong_password")
            )
            solr_admin_client.create_collection(collection_name="test_collection")

        assert "401 Client Error: Unauthorized for url" in str(excinfo.value)

    def test_successful_collection_creation(self):
        """Test successful collection creation."""
        cfg = MockSolrConfig()
        solr_admin_client = SolrAdminClient(cfg=cfg)
        collection_name = "test_collection"
        collection_url = solr_admin_client.create_collection(
            collection_name=collection_name
        )

        assert (
            collection_url
            == f"http://{cfg.SOLR_HOST}:{cfg.SOLR_PORT}/solr/{collection_name}"
        )

    def test_unsuccessful_collection_creation_empty_name(self):
        """Test unsuccessful collection creation due to empty name."""
        with pytest.raises(SolrValidationError) as excinfo:
            cfg = MockSolrConfig()
            solr_admin_client = SolrAdminClient(cfg=cfg)
            solr_admin_client.create_collection(collection_name="")
        assert "Collection name cannot be empty" in str(excinfo.value)

    def test_successful_return_collection_url_for_creating_collection_with_existing_name(
        self,
    ):
        """Test unsuccessful collection creation due to already existing collection."""
        cfg = MockSolrConfig()
        solr_admin_client = SolrAdminClient(cfg=cfg)
        collection_name = "test_collection"
        collection = solr_admin_client.create_collection(
            collection_name=collection_name
        )

        collection_dup = solr_admin_client.create_collection(
            collection_name=collection_name
        )
        assert collection == collection_dup

    def test_successful_delete_all_collections(self):
        """Test successful deletion of all collections."""
        cfg = MockSolrConfig()
        solr_admin_client = SolrAdminClient(cfg=cfg)
        collection_name = "test_collection"
        solr_admin_client.create_collection(collection_name=collection_name)
        response = solr_admin_client.delete_all_collections()

        assert response["responseHeader"]["status"] == 0

    def test_empty_response_upon_calling_deletion_solr_no_collections(self):
        """Test successful deletion of all collections."""
        cfg = MockSolrConfig()
        solr_admin_client = SolrAdminClient(cfg=cfg)
        solr_admin_client.delete_all_collections()

        response = solr_admin_client.delete_all_collections()

        assert response is None
