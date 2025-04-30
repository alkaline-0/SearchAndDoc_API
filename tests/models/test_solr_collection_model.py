import pytest

from db.solr_utils.solr_exceptions import SolrConnectionError, SolrValidationError
from models.solr_collection_model import SolrCollectionModel
from tests.db.mocks.mock_solr_config import MockSolrConfig


class TestSolrCollectionModel:

    def test_unsuccessful_model_obj_creation_empty_credentials(self):
        """Test unsuccessful collection creation due to wrong password."""
        with pytest.raises(SolrValidationError) as excinfo:
            cfg = MockSolrConfig(USER_NAME="", PASSWORD=" ")
            SolrCollectionModel(cfg=cfg)
        assert "Username/password cannot be empty or whitespace-only" in str(
            excinfo.value
        )

    def test_invalid_shard_rejection(self, solr_collection_model):
        with pytest.raises(SolrValidationError) as excinfo:
            solr_collection_model.create_collection(
                collection_name="test_invalid_shards", num_shards=-1, replicas_count=3
            )
        assert "Number of shards and replicas count must be greater than 0" in str(
            excinfo.value
        )

    def test_invalid_replica_rejection(self, solr_collection_model):
        with pytest.raises(SolrValidationError) as excinfo:
            solr_collection_model.create_collection(
                collection_name="test_invalid_replica", num_shards=2, replicas_count=-1
            )
        assert "Number of shards and replicas count must be greater than 0" in str(
            excinfo.value
        )

    def test_unsuccessful_collection_creation_empty_name(self, solr_collection_model):
        """Test unsuccessful collection creation due to empty name."""
        with pytest.raises(SolrValidationError) as excinfo:
            solr_collection_model.create_collection(
                collection_name="", num_shards=2, replicas_count=2
            )
        assert "Collection name cannot be empty" in str(excinfo.value)

    def test_unsuccessful_creation_of_model_with_existing_name(
        self, solr_collection_model
    ):
        """Test unsuccessful collection creation due to already existing collection."""
        with pytest.raises(SolrConnectionError) as excinfo:
            collection_name = "test_collection"
            solr_collection_model.create_collection(
                collection_name=collection_name, num_shards=1, replicas_count=1
            )

            solr_collection_model.create_collection(collection_name=collection_name)
            assert (
                "Cannot create a collection with the same name as existing one"
                in str(excinfo.value)
            )

    def test_unsuccessful_deletion_due_to_wrong_password(self, solr_collection_model):
        """Test unsuccessful deletion of all collections due to wrong password."""
        with pytest.raises(SolrConnectionError) as excinfo:
            collection_name = "test_collection"
            solr_collection_model.create_collection(collection_name="test_collection")

            cfg = MockSolrConfig(PASSWORD="wrong_password")
            SolrCollectionModel(cfg=cfg).delete_all_collections()
        assert "401 Client Error: Unauthorized for url" in str(excinfo.value)
        assert solr_collection_model.collection_exist(collection_name) is True

    def test_unsuccessful_collection_existence_check_due_to_wrong_password(self):
        """Test unsuccessful collection existence check due to wrong password."""
        with pytest.raises(SolrConnectionError) as excinfo:
            cfg = MockSolrConfig(PASSWORD="wrong_password")
            SolrCollectionModel(cfg=cfg).collection_exist(
                collection_name="test_collection"
            )
        assert "401 Client Error: Unauthorized for url" in str(excinfo.value)

    def test_unsuccessful_collection_creation_wrong_password(self):
        """Test unsuccessful collection creation due to wrong password."""
        with pytest.raises(SolrConnectionError) as excinfo:
            cfg = MockSolrConfig(PASSWORD="wrong_password")
            SolrCollectionModel(cfg=cfg).create_collection(
                collection_name="test_collection"
            )

        assert "401 Client Error: Unauthorized for url" in str(excinfo.value)

    def test_successful_collection_creation(self, solr_collection_model):
        """Test successful collection creation."""
        collection_name = "test_collection"
        collection_url = solr_collection_model.create_collection(
            collection_name=collection_name, replicas_count=1, num_shards=1
        )

        assert (
            collection_url
            == f"http://{MockSolrConfig().SOLR_HOST}:{MockSolrConfig().SOLR_PORT}/solr/{collection_name}"
        )
        assert solr_collection_model.collection_exist(collection_name) is True

    def test_successful_collection_deletion(self, solr_collection_model):
        """Test successful collection creation."""
        collection_name = "test_collection"
        solr_collection_model.create_collection(
            collection_name=collection_name, replicas_count=1, num_shards=1
        )

        solr_collection_model.delete_all_collections()
        assert solr_collection_model.collection_exist(collection_name) is False

    def test_successful_collection_existence_check(self, solr_collection_model):
        """Test successful collection existence check."""
        collection_name = "test_collection"
        solr_collection_model.create_collection(collection_name=collection_name)

        assert solr_collection_model.collection_exist(collection_name) is True

    def test_unsuccessful_collection_existence_check(self, solr_collection_model):
        """Test unsuccessful collection existence check."""

        collection_name = "non_existent_collection"

        assert solr_collection_model.collection_exist(collection_name) is False
