from unittest.mock import call, patch

import pytest

from services.create_collection_service import create_collection
from tests.db.mocks.mock_solr_config import MockSolrConfig


class TestCreateCollectionService:
    def test_successful_collection_creation(self, solr_connection):
        """Test successful collection creation."""
        collection_name = "test_collection"
        with patch.object(solr_connection, "_logger") as mock__logger:
            success = create_collection(
                server_id=collection_name,
                shards=1,
                replicas=1,
                logger=solr_connection._logger,
                cfg=MockSolrConfig(),
            )

        assert success is True
        mock__logger.info.assert_called_with(
            f"Created collection {collection_name} with 1 shards and 1 replicas."
        )
        assert (
            solr_connection.get_admin_client().collection_exist(collection_name) is True
        )

    def test_create_existing_collection(self, solr_connection):
        collection_name = "test_collection"
        with patch.object(solr_connection, "_logger") as mock_logger:
            create_collection(
                server_id=collection_name,
                shards=1,
                replicas=1,
                logger=solr_connection._logger,
                cfg=MockSolrConfig(),
            )
            failure = create_collection(
                server_id=collection_name,
                shards=1,
                replicas=1,
                logger=solr_connection._logger,
                cfg=MockSolrConfig(),
            )
        mock_logger.error.assert_has_calls(
            [call(f"Collection {collection_name} already exists.")]
        )
        assert failure is False

    def test_create_collection_with_invalid_parameters(self, solr_connection):
        with pytest.raises(Exception) as excinfo:
            collection_name = "test_collection"
            with patch.object(solr_connection, "_logger") as mock_logger:
                failure = create_collection(
                    server_id=collection_name,
                    shards=-1,
                    replicas=1,
                    logger=solr_connection._logger,
                    cfg=MockSolrConfig(),
                )
            assert "Failed to create collection:" in str(excinfo.value)
            mock_logger.error.assert_has_calls(
                [
                    call(
                        f"Failed to create collection: {str(excinfo.value)}",
                        exc_info=True,
                        stack_info=True,
                    )
                ]
            )
            assert failure is False
