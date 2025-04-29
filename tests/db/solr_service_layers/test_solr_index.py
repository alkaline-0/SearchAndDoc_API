import pytest

from db.solr_utils.solr_exceptions import SolrValidationError
from tests.db.conftest import RETRIEVER_MODEL
from tests.fixtures.test_data.fake_messages import documents


class TestSolrIndexing:

    def test_index_data_soft_commit_successfully(self, solr_client):
        solr_client.get_index_client(
            collection_name="test", retriever_model=RETRIEVER_MODEL
        ).index_data(documents, soft_commit=True)

        res = solr_client.get_index_client(
            collection_name="test", retriever_model=RETRIEVER_MODEL
        ).solr_client.search(q="*:*", rows=len(documents))

        assert res.docs is not None
        assert len(res.docs) == len(documents)
        assert res.docs[0]["bert_vector"] is not None

    def test_index_data_hard_commit_successfully(self, solr_client):
        solr_client.get_index_client(
            collection_name="test", retriever_model=RETRIEVER_MODEL
        ).index_data(documents, soft_commit=False)

        res = solr_client.get_index_client(
            collection_name="test", retriever_model=RETRIEVER_MODEL
        ).solr_client.search(q="*:*", rows=len(documents))

        assert res.docs is not None
        assert len(res.docs) == len(documents)
        assert res.docs[0]["bert_vector"] is not None

    def test_index_data_empty_data(self, solr_client):
        with pytest.raises(SolrValidationError) as exec_info:
            solr_client.get_index_client(
                collection_name="test", retriever_model=RETRIEVER_MODEL
            ).index_data([], soft_commit=True)
        assert "Data to index cannot be empty" in str(exec_info.value)
