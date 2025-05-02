import pytest

from db.utils.exceptions import SolrConnectionError, SolrValidationError
from models.solr_collection_model import SolrCollectionModel
from tests.db.mocks.mock_solr_config import MockSolrConfig


class TestSolrCollectionModel:

    def test_invalid_shard_rejection(self, solr_conn_factory_obj):
        with pytest.raises(SolrValidationError) as excinfo:
            solr_collection_model = SolrCollectionModel(
                collection_admin_service_obj=solr_conn_factory_obj.get_admin_client()
            )
            solr_collection_model.create_collection(
                collection_name="test_invalid_shards", num_shards=-1, replicas_count=3
            )
        assert "Number of shards and replicas count must be greater than 0" in str(
            excinfo.value
        )

    def test_invalid_replica_rejection(self, solr_conn_factory_obj):
        with pytest.raises(SolrValidationError) as excinfo:
            solr_collection_model = SolrCollectionModel(
                collection_admin_service_obj=solr_conn_factory_obj.get_admin_client()
            )
            solr_collection_model.create_collection(
                collection_name="test_invalid_replica", num_shards=2, replicas_count=-1
            )
        assert "Number of shards and replicas count must be greater than 0" in str(
            excinfo.value
        )

    def test_unsuccessful_collection_creation_empty_name(self, solr_conn_factory_obj):
        """Test unsuccessful collection creation due to empty name."""
        with pytest.raises(SolrValidationError) as excinfo:
            solr_collection_model = SolrCollectionModel(
                collection_admin_service_obj=solr_conn_factory_obj.get_admin_client()
            )
            solr_collection_model.create_collection(
                collection_name="", num_shards=2, replicas_count=2
            )
        assert "Collection name cannot be empty" in str(excinfo.value)

    def test_unsuccessful_creation_of_model_with_existing_name(
        self, solr_conn_factory_obj
    ):
        """Test unsuccessful collection creation due to already existing collection."""
        with pytest.raises(SolrConnectionError) as excinfo:
            solr_collection_model = SolrCollectionModel(
                collection_admin_service_obj=solr_conn_factory_obj.get_admin_client()
            )
            collection_name = "test_collection"
            solr_collection_model.create_collection(
                collection_name=collection_name, num_shards=1, replicas_count=1
            )

            solr_collection_model.create_collection(collection_name=collection_name)
            assert (
                "Cannot create a collection with the same name as existing one"
                in str(excinfo.value)
            )

    def test_successful_collection_creation(self, solr_conn_factory_obj):
        """Test successful collection creation."""
        solr_collection_model = SolrCollectionModel(
            collection_admin_service_obj=solr_conn_factory_obj.get_admin_client()
        )
        collection_name = "test_collection"
        collection_url = solr_collection_model.create_collection(
            collection_name=collection_name, replicas_count=1, num_shards=1
        )

        assert (
            collection_url
            == f"http://{MockSolrConfig().SOLR_HOST}:{MockSolrConfig().SOLR_PORT}/solr/{collection_name}"
        )
        assert solr_collection_model.collection_exist(collection_name) is True

    def test_successful_collection_deletion(self, solr_conn_factory_obj):
        """Test successful collection creation."""
        solr_collection_model = SolrCollectionModel(
            collection_admin_service_obj=solr_conn_factory_obj.get_admin_client()
        )
        collection_name = "test_collection"
        solr_collection_model.create_collection(
            collection_name=collection_name, replicas_count=1, num_shards=1
        )

        solr_collection_model.delete_all_collections()
        assert solr_collection_model.collection_exist(collection_name) is False

    def test_collection_exist_returns_true_for_existent_collection(
        self, solr_conn_factory_obj
    ):
        """Test successful collection existence check."""
        collection_name = "test_collection"
        solr_collection_model = SolrCollectionModel(
            collection_admin_service_obj=solr_conn_factory_obj.get_admin_client()
        )
        solr_collection_model.create_collection(collection_name=collection_name)

        assert solr_collection_model.collection_exist(collection_name) is True

    def test_collection_exist_returns_false_for_none_existent_collection(
        self, solr_conn_factory_obj
    ):
        """Test unsuccessful collection existence check."""
        solr_collection_model = SolrCollectionModel(
            collection_admin_service_obj=solr_conn_factory_obj.get_admin_client()
        )
        collection_name = "non_existent_collection"

        assert solr_collection_model.collection_exist(collection_name) is False
