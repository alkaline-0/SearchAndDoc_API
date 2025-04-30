import pytest

from db.solr_service_layers.solr_connection import SolrConnection
from db.solr_utils.solr_exceptions import (SolrConnectionError,
                                           SolrValidationError)
from models.solr_collection_model import SolrCollectionModel
from tests.db.mocks.mock_solr_config import MockSolrConfig
from tests.models import conftest


class TestSolrCollectionModel:
  def __init__(self):
    self._cfg = MockSolrConfig()
    self.collection_model = SolrCollectionModel(cfg=self._cfg, solr_conn_obj=self._solr_conn)
    
  def test_unsuccessful_model_obj_creation_empty_credentials(self, solr_client):
        """Test unsuccessful collection creation due to wrong password."""
        with pytest.raises(SolrValidationError) as excinfo:
            cfg = MockSolrConfig(USER_NAME="", PASSWORD=" ")
            SolrCollectionModel(cfg=cfg, solr_conn_obj=solr_client)
        assert "Username/password cannot be empty or whitespace-only" in str(
            excinfo.value
        )

  def test_invalid_shard_rejection(self):
        with pytest.raises(SolrValidationError) as excinfo:
            self.collection_model.create_new_collection(
                collection_name="test_invalid_shards", num_shards=-1, replicas_count=3
            )
        assert "Number of shards and replicas count must be greater than 0" in str(excinfo.value)

  def test_invalid_replica_rejection(self):
        with pytest.raises(SolrValidationError) as excinfo:
            self.collection_model.create_new_collection(
                collection_name="test_invalid_replica", num_shards=2, replicas_count=-1
            )
        assert "Number of shards and replicas count must be greater than 0" in str(excinfo.value)
        
  def test_unsuccessful_collection_creation_empty_name(self):
        """Test unsuccessful collection creation due to empty name."""
        with pytest.raises(SolrValidationError) as excinfo:
            self.collection_model.create_new_collection(collection_name="", num_shards=2, replicas_count=2)
        assert "Collection name cannot be empty" in str(excinfo.value)

  def test_unsuccessful_creation_of_model_with_existing_name(
        self,
    ):
    """Test unsuccessful collection creation due to already existing collection."""
    with pytest.raises(SolrConnectionError) as excinfo:
      collection_name = "test_collection"
      self.collection_model.create_new_collection(
          collection_name=collection_name, num_shards=1, replicas_count=1
      )

      self.collection_model.create_new_collection(
          collection_name=collection_name
      )
      assert "Cannot create a collection with the same name as existing one" in str(
        excinfo.value
    )
      
  def test_unsuccessful_deletion_of_all_collections_due_to_wrong_password(self):
        """Test unsuccessful deletion of all collections due to wrong password."""
        with pytest.raises(SolrConnectionError) as excinfo:
            collection_name = "test_collection"
            self.solr_conn.create_new_collection(collection_name="test_collection")
            
            cfg = MockSolrConfig(PASSWORD="wrong_password")
            new_conn = SolrConnection(cfg=cfg)
            SolrCollectionModel(cfg=cfg, solr_conn_obj=new_conn).delete_collections()
        assert "401 Client Error: Unauthorized for url" in str(excinfo.value)
        assert self.solr_conn.solr_admin_obj.collection_exist(collection_name) is True
        
  def test_unsuccessful_collection_existence_check_due_to_wrong_password(self):
        """Test unsuccessful collection existence check due to wrong password."""
        with pytest.raises(SolrConnectionError) as excinfo:
            cfg = MockSolrConfig(PASSWORD="wrong_password")
            new_conn = SolrConnection(cfg=cfg)
            SolrCollectionModel(cfg=cfg, solr_conn_obj=new_conn).collection_exist(collection_name="test_collection")
        assert "401 Client Error: Unauthorized for url" in str(excinfo.value)

  def test_unsuccessful_collection_creation_wrong_password(self):
    """Test unsuccessful collection creation due to wrong password."""
    with pytest.raises(SolrConnectionError) as excinfo:
        cfg = MockSolrConfig(PASSWORD="wrong_password")
        new_conn = SolrConnection(cfg=cfg)
        SolrCollectionModel(new_conn).create_new_collection(collection_name="test_collection")

    assert "401 Client Error: Unauthorized for url" in str(excinfo.value)
    
  def test_successful_collection_creation(self):
      """Test successful collection creation."""
      collection_name = "test_collection"
      collection_url = self.collection_model.create_new_collection(
          collection_name=collection_name, replicas_count=1, num_shards=1
      )

      assert (
          collection_url
          == f"http://{self.mock_config.SOLR_HOST}:{self.mock_config.SOLR_PORT}/solr/{collection_name}"
      )
      assert self.collection_model.collection_exist(collection_name) is True
      
  def test_successful_collection_deletion(self):
      """Test successful collection creation."""
      collection_name = "test_collection"
      collection_url = self.collection_model.create_new_collection(
          collection_name=collection_name, replicas_count=1, num_shards=1
      )

      self.collection_model.delete_collections()
      assert self.collection_model.collection_exist(collection_name) is False
      
  def test_successful_collection_existence_check(self):
      """Test successful collection existence check."""
      collection_name = "test_collection"
      self.collection_model.create_new_collection(collection_name=collection_name)

      assert self.collection_model.collection_exist(collection_name) is True

  def test_unsuccessful_collection_existence_check(self):
        """Test unsuccessful collection existence check."""

        collection_name = "non_existent_collection"

        assert self.collection_model.collection_exist(collection_name) is False