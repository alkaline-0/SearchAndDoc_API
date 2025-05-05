from unittest.mock import call, patch

from tests.fixtures.test_data.fake_messages import documents


class TestIndexDataService:

    def test_index_data_soft_commit_successfully(
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
        with patch.object(index_client, "_logger") as mock_logger:
            index_client.index_data(documents, soft_commit=True)

            rows_count = search_client.get_rows_count()

        mock_logger.info.assert_has_calls(
            [call(f"starting processing batch 0."), call(f"Indexed batch 0.")]
        )
        assert rows_count == len(documents)

    def test_index_data_hard_commit_successfully(
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

        with patch.object(index_client, "_logger") as mock_logger:
            index_client.index_data(documents, soft_commit=False)

            rows_count = search_client.get_rows_count()

        mock_logger.info.assert_has_calls(
            [call(f"starting processing batch 0."), call(f"Indexed batch 0.")]
        )
        rows_count = search_client.get_rows_count()
        assert rows_count == len(documents)
