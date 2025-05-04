from unittest.mock import call, patch

import pytest

from models.indexing_collection_model import IndexingCollectionModel
from models.semantic_search_model import SemanticSearchModel
from models.solr_collection_model import SolrCollectionModel
from services.config.config import MachineLearningModelConfig
from services.create_documentation_content_service import (
    CreateDocumentationContentService,
)
from services.machine_learning_model import AsyncGroqModel
from tests.fixtures.test_data.fake_messages import documents
from utils.get_logger import get_logger


class TestCreateDocumentationContentService:

    logger = get_logger()

    @pytest.mark.asyncio
    async def test_create_document_content_from_messages_successfully(
        self, solr_connection, retriever_model, rerank_model
    ):
        collection_admin_model = SolrCollectionModel(
            logger=self.logger,
            collection_admin_service_obj=solr_connection.get_admin_client(),
        )
        collection_url = collection_admin_model.create_collection(
            collection_name="test"
        )
        index_client = IndexingCollectionModel(
            self.logger,
            indexing_service_obj=solr_connection.get_index_client(
                retriever_model=retriever_model, collection_url=collection_url
            ),
        )
        search_client = SemanticSearchModel(
            self.logger,
            semantic_search_service_obj=solr_connection.get_search_client(
                collection_name="test",
                retriever_model=retriever_model,
                rerank_model=rerank_model,
                collection_url=collection_url,
            ),
        )

        index_client.index_data(documents, soft_commit=True)
        search_result = search_client.semantic_search(
            "web development project", threshold=0.1
        )

        groq_obj = AsyncGroqModel(self.logger, MachineLearningModelConfig())

        service_obj = CreateDocumentationContentService(
            ml_client=groq_obj, logger=search_client._logger
        )
        with patch.object(service_obj, "_logger") as mock_logger:
            result = await service_obj.create_document_content_from_messages(
                search_result, "test"
            )
        mock_logger.info.assert_called_with("Created README successfully.")
        print(result, flush=True)
        assert len(result) > 0
        assert "Overview" in "".join(result)

    @pytest.mark.asyncio
    async def test_catch_error_thrown_by_Model(
        self, solr_connection, retriever_model, rerank_model
    ):
        collection_admin_model = SolrCollectionModel(
            logger=self.logger,
            collection_admin_service_obj=solr_connection.get_admin_client(),
        )
        collection_url = collection_admin_model.create_collection(
            collection_name="test"
        )
        index_client = IndexingCollectionModel(
            self.logger,
            indexing_service_obj=solr_connection.get_index_client(
                retriever_model=retriever_model, collection_url=collection_url
            ),
        )
        search_client = SemanticSearchModel(
            self.logger,
            semantic_search_service_obj=solr_connection.get_search_client(
                collection_name="test",
                retriever_model=retriever_model,
                rerank_model=rerank_model,
                collection_url=collection_url,
            ),
        )

        index_client.index_data(documents, soft_commit=True)
        search_result = search_client.semantic_search(
            "web development project", threshold=0.1
        )

        groq_obj = AsyncGroqModel(self.logger, MachineLearningModelConfig())

        service_obj = CreateDocumentationContentService(
            ml_client=groq_obj, logger=search_client._logger
        )
        e = Exception("something went wrong")
        with (
            patch.object(groq_obj, "_model.chat.completions.create") as groq_mock,
            patch.object(service_obj, "_logger") as mock_logger,
        ):
            groq_mock.return_value = e
            groq_mock.side_effect = e

            result = await service_obj.create_document_content_from_messages(
                search_result, "test"
            )
        mock_logger.error.assert_called_with(
            [call(e), call(exc_info=True), call(stack_info=True)]
        )
        print(result, flush=True)
        assert len(result) > 0
        assert "Overview" in "".join(result)
