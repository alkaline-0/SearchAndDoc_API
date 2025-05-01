from unittest.mock import patch

import pytest

from db.solr_utils.solr_exceptions import SolrError
from tests.fixtures.test_data.fake_messages import documents


class TestSolrSearch:
    def test_threshold_filtering_semantic_search(
        self, solr_connection, retriever_model, rerank_model
    ):
        collection_url = solr_connection.get_admin_client().create_collection(
            collection_name="test"
        )
        search_client = solr_connection.get_search_client(
            collection_url=collection_url,
            rerank_model=rerank_model,
            retriever_model=retriever_model,
            collection_name="test",
        )

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
        with (
            patch.object(
                search_client,
                "_retrieve_docs_with_knn",
                return_value=mock_docs,
            ),
            patch.object(
                search_client,
                "_process_reranked_results",
                return_value=mock_scores,
            ),
        ):
            results = search_client.semantic_search(q="test", threshold=0.1)
        assert len(results) == 3  # text1, text2, text4 should pass
        assert {r["message_id"] for r in results} == {"id1", "id2", "id4"}

    def test_successful_semantic_search(
        self, solr_connection, retriever_model, rerank_model
    ):
        collection_url = solr_connection.get_admin_client().create_collection(
            collection_name="test"
        )
        index_client = solr_connection.get_index_client(
            collection_url=collection_url, retriever_model=retriever_model
        )
        search_client = solr_connection.get_search_client(
            collection_url=collection_url,
            rerank_model=rerank_model,
            retriever_model=retriever_model,
            collection_name="test",
        )

        index_client.index_data(documents, soft_commit=True)
        res = search_client.semantic_search(q="web backend implementation")
        assert res is not None
        assert len(res[0]["message_content"]) > 0

    def test_query_injection(self, solr_connection, rerank_model, retriever_model):
        with pytest.raises(SolrError) as excinfo:
            collection_url = solr_connection.get_admin_client().create_collection(
                collection_name="test"
            )
            search_client = solr_connection.get_search_client(
                collection_url=collection_url,
                rerank_model=rerank_model,
                retriever_model=retriever_model,
                collection_name="test",
            )

            search_client.semantic_search(q="test; DROP test")
        assert "Cannot perform this query" in str(excinfo.value)

        solr_admin = solr_connection.get_admin_client()
        assert solr_admin.collection_exist("test")

    def test_retrieve_all_docs_successfully(
        self, solr_connection, retriever_model, rerank_model
    ):
        collection_url = solr_connection.get_admin_client().create_collection(
            collection_name="test"
        )
        index_client = solr_connection.get_index_client(
            collection_url=collection_url, retriever_model=retriever_model
        )
        search_client = solr_connection.get_search_client(
            collection_url=collection_url,
            rerank_model=rerank_model,
            retriever_model=retriever_model,
            collection_name="test",
        )

        index_client.index_data(documents, soft_commit=True)
        res = search_client.retrieve_all_docs()
        assert (len(res)) == len(documents)
