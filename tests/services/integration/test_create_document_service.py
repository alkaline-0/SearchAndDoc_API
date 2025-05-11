from collections.abc import Iterator
from datetime import datetime
from unittest.mock import patch

import pytest

from db.infrastructure.connection_factory_service import ConnectionFactoryService
from db.utils.interfaces.sentence_transformer_interface import (
    SentenceTransformerInterface,
)
from services.config.config import MachineLearningModelConfig
from services.create_collection_service import (
    CreateCollectionServiceParams,
    create_collection_service,
)
from services.create_document_service import (
    CreateDocumentServiceParams,
    create_document_service,
)
from services.index_data_service import IndexDataServiceParams, index_data_service
from tests.db.mocks.mock_solr_config import MockSolrConfig
from tests.fixtures.test_data.fake_messages import documents


class TestCreateDocumentService:
    @pytest.mark.asyncio
    async def test_successful_document_creation(
        self,
        solr_connection: Iterator[ConnectionFactoryService],
        retriever_model: SentenceTransformerInterface,
        rerank_model: SentenceTransformerInterface,
    ):
        """Test end-to-end document creation workflow"""
        # Arrange
        collection_name = "test_docs"
        topic = "web development"
        with patch.object(solr_connection, "_logger") as mock_logger:
            # Create collection
            collection_params = CreateCollectionServiceParams(
                server_id=collection_name,
                shards=1,
                replicas=1,
                logger=mock_logger,
                cfg=MockSolrConfig(),
            )
            create_collection_service(params=collection_params)

            # Index sample data
            index_params = IndexDataServiceParams(
                server_id=collection_name,
                data=documents,
                logger=mock_logger,
                retriever_model=retriever_model,
                cfg=MockSolrConfig(),
            )
            index_data_service(params=index_params)

            # Prepare document creation params
            ml_config = MachineLearningModelConfig()
            doc_params = CreateDocumentServiceParams(
                server_id=collection_name,
                logger=mock_logger,
                topic=topic,
                retriever_model=retriever_model,
                rerank_model=rerank_model,
                cfg=MockSolrConfig(),
                ml_cfg=ml_config,
                start_date=datetime(2025, 4, 13),  # Future date
                end_date=datetime(2025, 4, 17),
            )

            # Act
            result = await create_document_service(params=doc_params)

            # Assert
            assert result is not None
            assert len(result) > 0
            mock_logger.info.assert_any_call(f"Found collection {collection_name}")
            mock_logger.info.assert_any_call("Document content created successfully")

    @pytest.mark.asyncio
    async def test_nonexistent_collection(
        self,
        solr_connection: Iterator[ConnectionFactoryService],
        retriever_model: SentenceTransformerInterface,
        rerank_model: SentenceTransformerInterface,
    ):
        """Test document creation with missing collection"""
        with patch.object(solr_connection, "_logger") as mock_logger:
            # Arrange
            ml_config = MachineLearningModelConfig()
            doc_params = CreateDocumentServiceParams(
                server_id="missing_collection",
                logger=mock_logger,
                topic="test",
                retriever_model=retriever_model,
                rerank_model=rerank_model,
                cfg=MockSolrConfig(),
                ml_cfg=ml_config,
            )

            # Act
            result = await create_document_service(params=doc_params)

            # Assert
            assert result is None
            mock_logger.error.assert_called_once_with(
                "Collection missing_collection does not exist."
            )

    @pytest.mark.asyncio
    async def test_search_failure(
        self,
        solr_connection: Iterator[ConnectionFactoryService],
        retriever_model: SentenceTransformerInterface,
        rerank_model: SentenceTransformerInterface,
    ):
        """Test invalid search parameters handling"""
        with patch.object(solr_connection, "_logger") as mock_logger:
            # Arrange
            collection_name = "test_docs"
            collection_params = CreateCollectionServiceParams(
                server_id=collection_name,
                shards=1,
                replicas=1,
                logger=mock_logger,
                cfg=MockSolrConfig(),
            )
            create_collection_service(params=collection_params)

            # Create params with invalid date range
            ml_config = MachineLearningModelConfig()
            doc_params = CreateDocumentServiceParams(
                server_id=collection_name,
                logger=mock_logger,
                topic="test",
                retriever_model=retriever_model,
                rerank_model=rerank_model,
                cfg=MockSolrConfig(),
                ml_cfg=ml_config,
                start_date=datetime(2025, 4, 19),  # Future date
                end_date=datetime(2025, 4, 25),
            )

            # Act/Assert
            with pytest.raises(Exception) as exc_info:
                await create_document_service(params=doc_params)

            assert "Search failed" in str(exc_info.value)
            mock_logger.error.assert_called_with(
                "Search failed: not enough values to unpack (expected 1, got 0)",
                exc_info=True,
            )
