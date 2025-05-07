from unittest.mock import call, patch

import pytest

from services.create_collection_service import (
    CreateCollectionServiceParams,
    create_collection_service,
)
from tests.db.mocks.mock_solr_config import MockSolrConfig


class TestCreateCollectionService:
    def test_successful_collection_creation(self, solr_connection):
        """Test successful collection creation."""
        collection_name = "test_collection"
        with patch.object(solr_connection, "_logger") as mock_logger:
            params = CreateCollectionServiceParams(
                server_id=collection_name,
                shards=1,
                replicas=1,
                logger=solr_connection._logger,
                cfg=MockSolrConfig(),
            )
            success = create_collection_service(params=params)

        assert success is True
        mock_logger.info.assert_called_with(
            f"Created collection {collection_name} with 1 shards and 1 replicas."
        )
        assert (
            solr_connection.get_admin_client().collection_exist(collection_name) is True
        )

    def test_create_existing_collection(self, solr_connection):
        collection_name = "test_collection"
        with patch.object(solr_connection, "_logger") as mock_logger:
            params = CreateCollectionServiceParams(
                server_id=collection_name,
                shards=1,
                replicas=1,
                logger=solr_connection._logger,
                cfg=MockSolrConfig(),
            )
            create_collection_service(params=params)
            failure = create_collection_service(
                params=params,
            )
        mock_logger.error.assert_has_calls(
            [call(f"Collection {collection_name} already exists.")]
        )
        assert failure is False

    def test_create_collection_with_invalid_parameters(self, solr_connection):
        with pytest.raises(Exception) as excinfo:
            collection_name = "test_collection"
            with patch.object(solr_connection, "_logger") as mock_logger:
                params = CreateCollectionServiceParams(
                    server_id=collection_name,
                    shards=-1,
                    replicas=1,
                    logger=solr_connection._logger,
                    cfg=MockSolrConfig(),
                )
                failure = create_collection_service(params=params)
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
