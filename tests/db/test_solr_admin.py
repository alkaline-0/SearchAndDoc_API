import pytest

from db.solr_utils.solr_admin import SolrAdminClient
from db.solr_utils.solr_exceptions import SolrConnectionError, SolrValidationError
from tests.db.mocks.mock_solr_config import MockSolrConfig


class TestSolrAdmin:

    def test_unsuccessful_collection_creation_wrong_password(self):
        """Test unsuccessful collection creation due to wrong password."""
        with pytest.raises(SolrConnectionError) as excinfo:
            solr_admin_client = SolrAdminClient(
                cfg=MockSolrConfig(PASSWORD="wrong_password")
            )
            solr_admin_client.create_collection(collection_name="test_collection")

        assert "401 Client Error: Unauthorized for url" in str(excinfo.value)

    def test_successful_collection_creation(self):
        """Test successful collection creation."""
        cfg = MockSolrConfig()
        solr_admin_client = SolrAdminClient(cfg=cfg)
        collection_name = "test_collection"
        collection_url = solr_admin_client.create_collection(
            collection_name=collection_name
        )

        assert (
            collection_url
            == f"http://{cfg.SOLR_HOST}:{cfg.SOLR_PORT}/solr/{collection_name}"
        )

    def test_unsuccessful_collection_creation_empty_name(self):
        """Test unsuccessful collection creation due to empty name."""
        with pytest.raises(SolrValidationError) as excinfo:
            cfg = MockSolrConfig()
            solr_admin_client = SolrAdminClient(cfg=cfg)
            solr_admin_client.create_collection(collection_name="")
        assert "Collection name cannot be empty" in str(excinfo.value)

    def test_successful_return_collection_url_for_creating_collection_with_existing_name(
        self,
    ):
        """Test unsuccessful collection creation due to already existing collection."""
        cfg = MockSolrConfig()
        solr_admin_client = SolrAdminClient(cfg=cfg)
        collection_name = "test_collection"
        collection = solr_admin_client.create_collection(
            collection_name=collection_name
        )

        collection_dup = solr_admin_client.create_collection(
            collection_name=collection_name
        )
        assert collection == collection_dup


# class TestSolrCore:
#     """Test Solr collection operations."""

#     def test_successful_indexing_of_data_with_soft_commit(self, solr_test_agent):

#         data = [
#             {
#                 "message_id": 1,
#                 "author_id": 101,
#                 "channel_id": 10,
#                 "message_content": "Hey everyone, good morning!",
#                 "created_at": "2025-04-14T08:30:00Z",
#             },
#             {
#                 "message_id": 2,
#                 "author_id": 102,
#                 "channel_id": 10,
#                 "message_content": "Good morning! How's it going?",
#                 "created_at": "2025-04-14T08:31:15Z",
#             },
#             {
#                 "message_id": 3,
#                 "author_id": 101,
#                 "channel_id": 11,
#                 "message_content": "Meeting starts in 10 minutes.",
#                 "created_at": "2025-04-14T08:32:00Z",
#             },
#             {
#                 "message_id": 4,
#                 "author_id": 103,
#                 "channel_id": 11,
#                 "message_content": "Got it, thanks for the heads-up!",
#                 "created_at": "2025-04-14T08:33:20Z",
#             },
#             {
#                 "message_id": 5,
#                 "author_id": 104,
#                 "channel_id": 12,
#                 "message_content": "Can someone share the project file?",
#                 "created_at": "2025-04-14T08:35:10Z",
#             },
#         ]

#         response = solr_test_agent.select_docs(query="*:*")
#         assert response is not None
#         solr_test_agent.index_data(data=data, soft_commit=True)
#         response = solr_test_agent.select_docs(query="*:*")
#         assert response is not None
#         assert len(response) == len(data)

#     def test_failed_indexing_of_data_with_empty_data(self, solr_test_agent):
#         with pytest.raises(ValueError) as excinfo:
#             solr_test_agent.index_data(data=[], soft_commit=False)
#         assert "Data to index cannot be empty" in str(excinfo.value)

#     def test_successful_indexing_of_data_with_hard_commit(self, solr_test_agent):
#         data = [
#             {
#                 "message_id": 1,
#                 "author_id": 101,
#                 "channel_id": 10,
#                 "message_content": "Hey everyone, good morning!",
#                 "created_at": "2025-04-14T08:30:00Z",
#             },
#             {
#                 "message_id": 2,
#                 "author_id": 102,
#                 "channel_id": 10,
#                 "message_content": "Good morning! How's it going?",
#                 "created_at": "2025-04-14T08:31:15Z",
#             },
#             {
#                 "message_id": 3,
#                 "author_id": 101,
#                 "channel_id": 11,
#                 "message_content": "Meeting starts in 10 minutes.",
#                 "created_at": "2025-04-14T08:32:00Z",
#             },
#             {
#                 "message_id": 4,
#                 "author_id": 103,
#                 "channel_id": 11,
#                 "message_content": "Got it, thanks for the heads-up!",
#                 "created_at": "2025-04-14T08:33:20Z",
#             },
#             {
#                 "message_id": 5,
#                 "author_id": 104,
#                 "channel_id": 12,
#                 "message_content": "Can someone share the project file?",
#                 "created_at": "2025-04-14T08:35:10Z",
#             },
#         ]

#         response = solr_test_agent.select_docs(query="*:*")
#         assert response is not None
#         solr_test_agent.index_data(data=data, soft_commit=False)

#         response = solr_test_agent.select_docs(query="*:*")
#         assert response is not None
#         assert len(response) == len(data)
