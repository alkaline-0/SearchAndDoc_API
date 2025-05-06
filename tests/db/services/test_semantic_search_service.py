from datetime import datetime
from unittest.mock import call, patch

import pytest

from db.utils.exceptions import SolrError
from tests.fixtures.test_data.fake_messages import documents


class TestSemanticSearchService:
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
            patch.object(search_client, "_logger") as mock_logger,
        ):
            results = search_client.semantic_search(q="test", threshold=0.1)

        mock_logger.info.assert_has_calls(
            [
                call("Created the embeddings for the query."),
                call("Retrieved docs from solr successfully."),
                call("Reranked results from solr successfully."),
            ]
        )
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
        solr_date_format = "%Y-%m-%dT%H:%M:%SZ"
        start_date = datetime(2025, 4, 13)
        end_date = datetime(2025, 4, 17)
        with patch.object(search_client, "_logger") as mock_logger:
            index_client.index_data(documents, soft_commit=True)
            res = search_client.semantic_search(
                q="web backend implementation",
                start_date=start_date,  # Future date
                end_date=end_date,
            )
            mock_logger.info.assert_has_calls(
                [
                    call("Created the embeddings for the query."),
                    call(
                        "Retrieved docs from solr successfully.",
                    ),
                    call(
                        "Reranked results from solr successfully.",
                    ),
                ]
            )
        assert res is not None
        assert len(res[0]["message_content"]) > 0
        assert all(
            datetime.strptime(item["created_at"], solr_date_format).date()
            >= start_date.date()
            and datetime.strptime(item["created_at"], solr_date_format).date()
            <= end_date.date()
            for item in res
        )

    def test_query_injection(self, solr_connection, rerank_model, retriever_model):
        collection_url = solr_connection.get_admin_client().create_collection(
            collection_name="test"
        )
        with pytest.raises(SolrError) as excinfo:
            search_client = solr_connection.get_search_client(
                collection_url=collection_url,
                rerank_model=rerank_model,
                retriever_model=retriever_model,
                collection_name="test",
            )
            with patch.object(search_client, "_logger") as mock_logger:
                search_client.semantic_search(q="test; DROP test")

            mock_logger.error.assert_has_calls(
                [
                    call(
                        f"Query contains invalid characters test; DROP test",
                    )
                ]
            )
        assert "Cannot perform this query" in str(excinfo.value)

        solr_admin = solr_connection.get_admin_client()
        assert solr_admin.collection_exist("test")

    def test_unsuccessful_semantic_search_due_to_solr_error(
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
        with (
            patch.object(search_client, "_logger") as mock_logger,
            patch.object(search_client.solr_client, "search") as solr_mock,
            pytest.raises(Exception) as excinfo,
        ):
            e = Exception("Something went wrong!")
            solr_mock.return_value = e
            solr_mock.side_effect = e

            index_client.index_data(documents, soft_commit=True)
            search_client.semantic_search(q="web backend implementation")
        mock_logger.error.assert_has_calls([call(e, stack_info=True, exec_info=True)])
        assert "Something went wrong!" in str(excinfo.value)
