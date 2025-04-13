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

    def connection_fails_with_invalid_credentials(self) -> None:
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
