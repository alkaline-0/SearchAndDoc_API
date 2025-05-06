from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest

from db.services.connection_factory_service import ConnectionFactoryService
from db.utils.interfaces.sentence_transformer_interface import (
    SentenceTransformerInterface,
)
from services.create_collection_service import (
    CreateCollectionServiceParams,
    create_collection,
)
from services.index_data_service import IndexDataServiceParams, index_data_service
from tests.db.mocks.mock_solr_config import MockSolrConfig
from tests.fixtures.test_data.fake_messages import documents


class TestIndexDataService:
    def test_successful_indexing(
        self,
        solr_connection: Iterator[ConnectionFactoryService],
        retriever_model: SentenceTransformerInterface,
    ):
        """Test successful indexing workflow"""
        # Arrange
        collection_name = "test_collection"
        with patch.object(solr_connection, "_logger") as mock_logger:
            params = CreateCollectionServiceParams(
                server_id=collection_name,
                shards=1,
                replicas=1,
                logger=solr_connection._logger,
                cfg=MockSolrConfig(),
            )
            create_collection(params=params)

            # Act
            index_data_service_params = IndexDataServiceParams(
                server_id="test_collection",
                data=documents,
                logger=mock_logger,
                retriever_model=retriever_model,
                cfg=MockSolrConfig(),
            )
            result = index_data_service(params=index_data_service_params)

        # Assert
        assert result is True
        mock_logger.info.assert_any_call(
            "Found the collection test_collection, proceeding with indexing"
        )
        mock_logger.info.assert_any_call(
            "Indexing the data without storing in the hard driver for speed."
        )
        mock_logger.info.assert_any_call(
            "soft commit indexing finished successfully, spawning a process to store to hard disk "
        )
        assert (
            solr_connection.get_admin_client().collection_exist(collection_name) is True
        )

    def test_index_nonexistent_collection(
        self,
        solr_connection: Iterator[ConnectionFactoryService],
        retriever_model: SentenceTransformerInterface,
    ):
        """Test indexing to non-existent collection"""
        with patch.object(solr_connection, "_logger") as mock_logger:
            # Act
            index_data_service_params = IndexDataServiceParams(
                server_id="test_collection",
                data=documents,
                logger=mock_logger,
                retriever_model=retriever_model,
                cfg=MockSolrConfig(),
            )
            result = index_data_service(params=index_data_service_params)

        # Assert
        assert result is False
        mock_logger.error.assert_called_once_with(
            "Collection test_collection does not exist."
        )

    def test_indexing_exception_propagation(
        self,
        solr_connection: Iterator[ConnectionFactoryService],
    ):
        """Test exception handling during indexing"""
        # Arrange
        collection_name = "test_collection"
        with patch.object(solr_connection, "_logger") as mock_logger:
            params = CreateCollectionServiceParams(
                server_id=collection_name,
                shards=1,
                replicas=1,
                logger=solr_connection._logger,
                cfg=MockSolrConfig(),
            )
            create_collection(params=params)
            # Act/Assert
            with pytest.raises(Exception) as excinfo:
                index_data_service_params = IndexDataServiceParams(
                    server_id="test_collection",
                    data=[{}],
                    logger=mock_logger,
                    retriever_model=MagicMock(),
                    cfg=MockSolrConfig(),
                )
                index_data_service(params=index_data_service_params)

        mock_logger.error.assert_called_with(
            "Failed to index data in index data service", exc_info=True, stack_info=True
        )
