import pytest

from db.solr_utils.solr_exceptions import SolrValidationError
from models.indexing_collection_model import IndexingCollectionModel
from models.semantic_search_model import SemanticSearchModel
from models.solr_collection_model import SolrCollectionModel
from tests.db.mocks.mock_solr_config import MockSolrConfig
from tests.fixtures.test_data.fake_messages import documents
from tests.models import conftest


class TestSemanticSearchModel:
  def __init__(self):
    self._cfg = MockSolrConfig()
    self._collection_url = SolrCollectionModel(cfg=self._cfg, solr_conn_obj=conftest.solr_client).create_new_collection("test_collection", num_shards=1, replicas_count=1)
    IndexingCollectionModel(cfg=self._cfg, solr_conn=conftest.solr_client, collection_url=self._collection_url, retriever_model=conftest.RETRIEVER_MODEL).index_data(documents=documents, soft_commit=True)
    self.semantic_search_model = SemanticSearchModel(cfg = self._cfg, collection_url=self._collection_url, collection_name="test_collection", retriever_model=conftest.RETRIEVER_MODEL, rerank_model=conftest.RERANK_MODEL)

  def test_successful_semantic_search(self):
      res = self.semantic_search_model.semantic_search(q="web backend implementation")
      assert res is not None
      assert len(res[0]["message_content"]) > 0
    
  def test_retrieve_all_docs_successfully(self):
    res=self.semantic_search_model.retrieve_all_docs()
    assert (len(res)) == len(documents)
    
  def test_unsuccesful_search_due_to_invalid_query(self):
        """Test unsuccessful collection existence check due to wrong password."""
        with pytest.raises(SolrValidationError) as excinfo:
          self.semantic_search_model.semantic_search(" ")
        assert "Search query must be only english letters" in str(excinfo.value)
        
  def test_unsuccesful_search_due_to_numbers_query(self):
        """Test unsuccessful collection existence check due to wrong password."""
        with pytest.raises(SolrValidationError) as excinfo:
          self.semantic_search_model.semantic_search("123testback")
        assert "Search query must be only english letters" in str(excinfo.value)
        
  def test_empty_query_semantic_search(self, solr_client):
        with pytest.raises(SolrValidationError) as exec_info:
            self.semantic_search_model.semantic_search(q="")
        assert "Search query must be at least 4 letters" in str(exec_info.value)