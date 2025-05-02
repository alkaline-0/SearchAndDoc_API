import pytest
from groq import AsyncGroq

from models.indexing_collection_model import IndexingCollectionModel
from models.semantic_search_model import SemanticSearchModel
from models.solr_collection_model import SolrCollectionModel
from services.config.groq_config import GroqConfig
from services.create_documentation_content_service import (
    CreateDocumentationContentService,
)
from tests.fixtures.test_data.fake_messages import documents


class TestCreateDocumentationContentService:

    @pytest.mark.asyncio
    async def test_create_document_content_from_messages_successfully(
        self, solr_connection, retriever_model, rerank_model
    ):
        collection_admin_model = SolrCollectionModel(solr_connection.get_admin_client())
        collection_url = collection_admin_model.create_collection(
            collection_name="test"
        )
        index_client = IndexingCollectionModel(
            indexing_service_obj=solr_connection.get_index_client(
                retriever_model=retriever_model, collection_url=collection_url
            )
        )
        search_client = SemanticSearchModel(
            semantic_search_service_obj=solr_connection.get_search_client(
                collection_name="test",
                retriever_model=retriever_model,
                rerank_model=rerank_model,
                collection_url=collection_url,
            )
        )

        index_client.index_data(documents, soft_commit=True)
        search_result = search_client.semantic_search("web development project")
        cfg = GroqConfig()
        groq_obj = AsyncGroq(api_key=cfg.API_TOKEN)
        service_obj = CreateDocumentationContentService(
            groq_client=groq_obj, groq_config=cfg
        )
        result = await service_obj.create_document_content_from_messages(
            search_result, "test"
        )

        assert len(result) > 0
        assert "Overview" in "".join(result)
