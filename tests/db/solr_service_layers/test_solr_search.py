from unittest.mock import patch

import pytest

from db.solr_service_layers.solr_admin import SolrAdminClient
from db.solr_utils.solr_exceptions import SolrError
from tests.db.conftest import RERANK_MODEL, RETRIEVER_MODEL
from tests.fixtures.test_data.fake_messages import documents


class TestSolrSearch:
    def test_threshold_filtering_semantic_search(self, solr_client):
        mock_scores = [
            (
                {"message_content": "text1", "message_id": "id1"},
                0.1999,
            ),
            (
                {"message_content": "text2", "message_id": "id2"},
                0.20005,
            ),
            (
                {"message_content": "text3", "message_id": "id3"},
                0.021,
            ),
            (
                {"message_content": "text4", "message_id": "id4"},
                0.205,
            ),
        ]
        mock_docs = [
            [
                {"message_content": "text1", "message_id": "id1"},
                {
                    "message_content": "text2",
                    "message_id": "id2",
                },
                {
                    "message_content": "text3",
                    "message_id": "id3",
                },
                {
                    "message_content": "text4",
                    "message_id": "id4",
                },
            ]
        ]
        search_client = solr_client.get_search_client(
            collection_name="test",
            retriever_model=RETRIEVER_MODEL,
            rerank_model=RERANK_MODEL,
        )
        with (
            patch.object(
                search_client,
                "_retrieve_docs_with_knn",
                return_value=mock_docs,
            ),
            patch.object(
                search_client, "_process_reranked_results", return_value=mock_scores
            ),
        ):
            results = search_client.semantic_search(q="test", threshold=0.1)
        assert len(results) == 3  # text1, text2, text4 should pass
        assert {r["message_id"] for r in results} == {"id1", "id2", "id4"}

    def test_successful_semantic_search(self, solr_client):
        solr_client.get_index_client(
            "test", retriever_model=RETRIEVER_MODEL
        ).index_data(documents, soft_commit=True)
        res = solr_client.get_search_client(
            collection_name="test",
            retriever_model=RETRIEVER_MODEL,
            rerank_model=RERANK_MODEL,
        ).semantic_search(q="web backend implementation")
        assert res is not None
        assert len(res[0]["message_content"]) > 0

    def test_query_injection(self, solr_client):
        with pytest.raises(SolrError) as excinfo:
            solr_client.get_search_client(
                collection_name="test",
                retriever_model=RETRIEVER_MODEL,
                rerank_model=RERANK_MODEL,
            ).semantic_search(q="test; DROP test")
            assert "Cannot perform this query" in excinfo.value()

            solr_admin = SolrAdminClient(
                solr_client.get_search_client(
                    collection_name="test",
                    retriever_model=RETRIEVER_MODEL,
                    rerank_model=RERANK_MODEL,
                ).cfg
            )
            assert solr_admin.collection_exist("test")  # Verify query sanitization

    def test_commit_behavior(self, solr_client):
        """Verify documents are immediately searchable after insertion."""

        solr_client.get_search_client(
            collection_name="test",
            retriever_model=RETRIEVER_MODEL,
            rerank_model=RERANK_MODEL,
        ).solr_client.add(documents)

        results = solr_client.get_search_client(
            collection_name="test",
            retriever_model=RETRIEVER_MODEL,
            rerank_model=RERANK_MODEL,
        ).solr_client.search("message_id:5")
        assert len(results) == 1  # Fails if always_commit isn't working

    def test_retrieve_all_docs_successfully(self, solr_client):
        solr_client.get_index_client(
            "test", retriever_model=RETRIEVER_MODEL
        ).index_data(documents, soft_commit=True)
        [res] = solr_client.get_search_client(
            collection_name="test",
            retriever_model=RETRIEVER_MODEL,
            rerank_model=RERANK_MODEL,
        ).retrieve_all_docs()
        assert (len(res)) == len(documents)
