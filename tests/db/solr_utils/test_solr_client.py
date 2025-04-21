import pytest
from db.solr_utils.solr_exceptions import SolrConnectionError, SolrValidationError, SolrRequestError
from tests.fixtures.test_data.fake_messages import documents

class TestSolrClient:
    def test_index_data_soft_commit_successfully(self, solr_test_agent):
        solr_test_agent.index_data(documents, soft_commit=True)

        res = solr_test_agent.solr_client.search(q="*:*", rows = len(documents))
        
        assert res.docs is not None
        assert len(res.docs) == len(documents)
        assert res.docs[0]["bert_vector"] is not None
        assert res.docs[0]["message_content"] == documents[0]["message_content"]
  
    def test_index_data_hard_commit_successfully(self, solr_test_agent):
        solr_test_agent.index_data(documents, soft_commit=False)

        res = solr_test_agent.solr_client.search(q="*:*", rows = len(documents))
        
        assert res.docs is not None
        assert len(res.docs) == len(documents)
        assert res.docs[0]["bert_vector"] is not None
        assert res.docs[0]["message_content"] == documents[0]["message_content"]
        
    def test_index_data_empty_data(self, solr_test_agent):
        with pytest.raises(SolrValidationError) as exec_info:
            solr_test_agent.index_data([], soft_commit=True)
        assert "Data to index cannot be empty" in str(exec_info.value)
  
 