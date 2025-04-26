from unittest.mock import patch

import pysolr
import pytest
import torch

from db.solr_service_layers.solr_admin import SolrAdminClient
from db.solr_utils.solr_exceptions import SolrError, SolrValidationError
from tests.fixtures.test_data.fake_messages import documents


class TestSolrSearch:
    def test_empty_query_semantic_search(self, solr_client):
        with pytest.raises(SolrValidationError) as exec_info:
            solr_client.get_search_client("test").semantic_search(
                q="", row_begin=0, row_end=10
            )
        assert "Query string cannot be empty" in str(exec_info.value)

    def test_negative_row_begin_semantic_search(self, solr_client):
        with pytest.raises(SolrValidationError) as exec_info:
            solr_client.get_search_client("test").semantic_search(
                q="test", row_begin=-1, row_end=10
            )
        assert "Row begin must be non-negative" in str(exec_info.value)

    def test_row_end_less_than_row_begin_semantic_search(self, solr_client):
        with pytest.raises(SolrValidationError) as exec_info:
            solr_client.get_search_client("test").semantic_search(
                q="test", row_begin=10, row_end=5
            )
        assert "Row end must be greater than row begin" in str(exec_info.value)

    def test_threshold_filtering_semantic_search(self, solr_client):
        mock_scores = [
            ("text1", 0.1999, "id1"),
            ("text2", 0.20005, "id2"),  # 0.20005 → round(0.20005, 2) = 0.20 → included
            ("text3", 0.05, "id3"),  # 0.194 → round(0.194, 2) = 0.19 → excluded
            ("text4", 0.205, "id4"),  # 0.205 → round(0.205, 2) = 0.21 → included
        ]
        search_client = solr_client.get_search_client("test")
        with patch.object(
            search_client, "_rerank_knn_results", return_value=mock_scores
        ):
            results = search_client.semantic_search(
                q="test", row_begin=0, row_end=10, threshold=0.1
            )
        assert len(results) == 3  # text1, text2, text4 should pass
        assert {r["message_id"] for r in results} == {"id1", "id2", "id4"}

    def test_reranking_order(self, solr_client):
        mock_docs = pysolr.Results(
            {
                "response": {
                    "docs": [
                        {"message_id": "1", "message_content": "bad match"},
                        {"message_id": "2", "message_content": "good match"},
                    ]
                }
            }
        )
        search_client = solr_client.get_search_client("test")
        with (
            patch.object(
                search_client,
                "_retrieve_docs_with_knn",
                return_value=mock_docs,
            ),
            patch.object(
                search_client.rerank_model,
                "encode",  # Second-stage model
            ) as mock_reranker_encode,
        ):
            content_encode = torch.tensor([[0.1] * 768, [0.9] * 768])
            query_encode = torch.tensor([[0.9] * 768])
            mock_reranker_encode.side_effect = [query_encode, content_encode]

            results = search_client.semantic_search(q="test", row_begin=0, row_end=2)
            print(results)

            assert [r["message_id"] for r in results] == ["2", "1"]

    def test_successful_semantic_search(self, solr_client):
        solr_client.get_index_client("test").index_data(documents, soft_commit=True)
        res = solr_client.get_search_client("test").semantic_search(
            q="web backend implementation", row_begin=0, row_end=100, top_k=1000
        )
        assert res is not None
        assert len(res[0]["message_content"]) > 0

    def test_query_injection(self, solr_client):
        with pytest.raises(SolrError) as excinfo:
            solr_client.get_search_client("test").semantic_search(
                q="test; DROP test", row_begin=0, row_end=10
            )
            assert "Cannot perform this query" in excinfo.value()

            solr_admin = SolrAdminClient(solr_client.get_search_client("test").cfg)
            assert solr_admin.collection_exist("test")  # Verify query sanitization

    def test_commit_behavior(self, solr_client):
        """Verify documents are immediately searchable after insertion."""

        solr_client.get_search_client("test").solr_client.add(documents)

        results = solr_client.get_search_client("test").solr_client.search(
            "message_id:5"
        )
        assert len(results) == 1  # Fails if always_commit isn't working
