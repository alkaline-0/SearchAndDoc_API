import pytest

from db.solr_utils.solr_exceptions import SolrValidationError
from models.indexing_collection_model import IndexingCollectionModel
from models.semantic_search_model import SemanticSearchModel
from models.solr_collection_model import SolrCollectionModel
from tests.db.mocks.mock_solr_config import MockSolrConfig
from tests.fixtures.test_data.fake_messages import documents
from tests.models import conftest


class TestSolrIndexingCollectionModel:
  def __init__(self):
    self._cfg = MockSolrConfig()
    self._collection_url = SolrCollectionModel(cfg=self._cfg, solr_conn_obj=conftest.solr_client).create_new_collection("test_collection", num_shards=1, replicas_count=1)
    
    self.indexing_model = IndexingCollectionModel(cfg=self._cfg, solr_conn=conftest.solr_client, collection_url=self._collection_url, retriever_model=conftest.RETRIEVER_MODEL)

  def test_index_data_soft_commit_successfully(self):
        
        self.indexing_model.index_data(documents, soft_commit=True)

        res = SemanticSearchModel(cfg = self._cfg, collection_url=self._collection_url, collection_name="test_collection", retriever_model=conftest.RETRIEVER_MODEL, rerank_model=conftest.RERANK_MODEL).retriece_all_docs()

        assert res is not None
        assert len(res) == len(documents)

  def test_index_data_hard_commit_successfully(self):
      self.indexing_model.index_data(documents, soft_commit=False)

      res = SemanticSearchModel(cfg = self._cfg, collection_url=self._collection_url, collection_name="test_collection", retriever_model=conftest.RETRIEVER_MODEL, rerank_model=conftest.RERANK_MODEL).retriece_all_docs()

      assert res.docs is not None
      assert len(res.docs) == len(documents)

    
  def test_index_data_empty_data(self, solr_client):
        with pytest.raises(SolrValidationError) as exec_info:
            self.indexing_model.index_data([], soft_commit=True)
        assert "Data to index cannot be empty" in str(exec_info.value)
