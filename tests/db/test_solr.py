import os

import fixtup
import pytest
import requests

from db.solr import Solr


class TestSolrObjectCreation:
    """Test Solr authentication scenarios."""

    def creation_fails_with_empty_values(self) -> None:
        with pytest.raises(ValueError) as excinfo:
            Solr(user_name="", password="", solr_host="", solr_port="")
        assert "All connection parameters are required" in str(excinfo.value)


class TestSolrAuthentication:
    """Test Solr authentication scenarios."""

    def connection_fails_with_invalmessage_id_credentials(self) -> None:
        with fixtup.up("solr"):
            with pytest.raises(requests.exceptions.HTTPError) as excinfo:
                client = Solr(
                    user_name=os.getenv("USER_NAME"),
                    password="wrong_password",
                    solr_host=os.getenv("SOLR_HOST_TEST"),
                    solr_port=os.getenv("SOLR_PORT_TEST"),
                )

                client.create_collection("test_collection")
            assert "401 Client Error: Unauthorized for url" in str(excinfo.value)


class TestSolrCollection:
    """Test Solr collection operations."""

    def test_creates_collection_successfully(self, solr_test_client) -> None:
        solr_test_client.create_collection("test_collection")
        assert solr_test_client.collection_exist("test_collection") is True

    def test_failed_collection_creation_existing_name(self, solr_test_client):
        solr_test_client.create_collection("test_collection")
        res = solr_test_client.create_collection("test_collection")
        assert res is None

    def test_failed_collection_creation_empty_name(self, solr_test_client):
        with pytest.raises(ValueError) as excinfo:
            solr_test_client.create_collection("")
        assert "Collection name cannot be empty" in str(excinfo.value)


class TestSolrCore:
    """Test Solr collection operations."""

    def test_successful_creation_of_solr_core(self, solr_test_client):
        solr_test_client.create_collection("new_col")
        res = solr_test_client.create_new_core("test_core", "new_col")
        assert res is not None
        assert res["responseHeader"]["status"] == 0

    def test_successful_indexing_of_data_with_soft_commit(self, solr_test_client):
        solr_test_client.create_collection("new_col")
        res = solr_test_client.create_new_core("test_core", "new_col")
        assert res is not None
        assert res["responseHeader"]["status"] == 0

        data = [
            {
                "message_id": 1,
                "author_id": 101,
                "channel_id": 10,
                "message_content": "Hey everyone, good morning!",
                "created_at": "2025-04-14T08:30:00Z",
            },
            {
                "message_id": 2,
                "author_id": 102,
                "channel_id": 10,
                "message_content": "Good morning! How's it going?",
                "created_at": "2025-04-14T08:31:15Z",
            },
            {
                "message_id": 3,
                "author_id": 101,
                "channel_id": 11,
                "message_content": "Meeting starts in 10 minutes.",
                "created_at": "2025-04-14T08:32:00Z",
            },
            {
                "message_id": 4,
                "author_id": 103,
                "channel_id": 11,
                "message_content": "Got it, thanks for the heads-up!",
                "created_at": "2025-04-14T08:33:20Z",
            },
            {
                "message_id": 5,
                "author_id": 104,
                "channel_id": 12,
                "message_content": "Can someone share the project file?",
                "created_at": "2025-04-14T08:35:10Z",
            },
        ]

        response = solr_test_client.select_docs(query="*:*", core_name="test_core")
        assert response is not None
        assert response["response"]["numFound"] == 0
        solr_test_client.index_data(data=data, core_name="test_core")

        response = solr_test_client.select_docs(query="*:*", core_name="test_core")
        assert response is not None
        assert response["response"]["numFound"] == len(data)

    def test_failed_indexing_of_data_with_empty_core_name(self, solr_test_client):
        with pytest.raises(ValueError) as excinfo:
            solr_test_client.index_data(data=["test"], core_name="")
        assert "Core name cannot be empty" in str(excinfo.value)

    def test_failed_indexing_of_data_with_empty_data(self, solr_test_client):
        with pytest.raises(ValueError) as excinfo:
            solr_test_client.index_data(data=[], core_name="test_core")
        assert "Data to index cannot be empty" in str(excinfo.value)

    def test_failed_indexing_of_data_with_non_existent_core(self, solr_test_client):
        with pytest.raises(ValueError) as excinfo:
            solr_test_client.index_data(data=["test"], core_name="non_existent_core")
        assert "Core does not exist" in str(excinfo.value)

    def test_failed_indexing_hard_commit_with_empty_core_name(self, solr_test_client):
        with pytest.raises(ValueError) as excinfo:
            solr_test_client.index_data_with_hard_commit(data=["test"], core_name="")
        assert "Core name cannot be empty" in str(excinfo.value)

    def test_failed_indexing_hard_commit_with_empty_data(self, solr_test_client):
        with pytest.raises(ValueError) as excinfo:
            solr_test_client.index_data_with_hard_commit(data=[], core_name="test_core")
        assert "Data to index cannot be empty" in str(excinfo.value)

    def test_failed_indexing_hard_commit_non_existent_core(self, solr_test_client):
        with pytest.raises(ValueError) as excinfo:
            solr_test_client.index_data_with_hard_commit(
                data=["test"], core_name="test_core"
            )
            assert "Data to index cannot be empty" in str(excinfo.value)

    def test_successful_indexing_of_data_with_hard_commit(self, solr_test_client):
        solr_test_client.create_collection("new_col")
        res = solr_test_client.create_new_core("test_core", "new_col")
        assert res is not None
        assert res["responseHeader"]["status"] == 0

        data = [
            {
                "message_id": 1,
                "author_id": 101,
                "channel_id": 10,
                "message_content": "Hey everyone, good morning!",
                "created_at": "2025-04-14T08:30:00Z",
            },
            {
                "message_id": 2,
                "author_id": 102,
                "channel_id": 10,
                "message_content": "Good morning! How's it going?",
                "created_at": "2025-04-14T08:31:15Z",
            },
            {
                "message_id": 3,
                "author_id": 101,
                "channel_id": 11,
                "message_content": "Meeting starts in 10 minutes.",
                "created_at": "2025-04-14T08:32:00Z",
            },
            {
                "message_id": 4,
                "author_id": 103,
                "channel_id": 11,
                "message_content": "Got it, thanks for the heads-up!",
                "created_at": "2025-04-14T08:33:20Z",
            },
            {
                "message_id": 5,
                "author_id": 104,
                "channel_id": 12,
                "message_content": "Can someone share the project file?",
                "created_at": "2025-04-14T08:35:10Z",
            },
        ]

        response = solr_test_client.select_docs(query="*:*", core_name="test_core")
        assert response is not None
        assert response["response"]["numFound"] == 0
        solr_test_client.index_data_with_hard_commit(data=data, core_name="test_core")

        response = solr_test_client.select_docs(query="*:*", core_name="test_core")
        assert response is not None
        assert response["response"]["numFound"] == len(data)
