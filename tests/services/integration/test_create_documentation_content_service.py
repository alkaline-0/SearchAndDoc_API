import asyncio

import pytest
from groq import AsyncGroq

from models.indexing_collection_model import IndexingCollectionModel
from models.semantic_search_model import SemanticSearchModel
from services.config.groq_config import GroqConfig
from services.create_documentation_content_service import \
    CreateDocumentationContentService
from tests.db.mocks.mock_solr_config import MockSolrConfig
from tests.fixtures.test_data.fake_messages import documents


class TestCreateDocumentationContentService:
    
  @pytest.mark.asyncio
  async def test_create_document_content_from_messages_successfully(
        self, solr_collection_model, retriever_model, rerank_model
    ):
        collection_url = solr_collection_model.create_collection(
            collection_name="test"
        )
        solr_cfg=MockSolrConfig()
        index_client = IndexingCollectionModel(
            collection_url=collection_url, retriever_model=retriever_model,cfg=solr_cfg
        )
        search_client = SemanticSearchModel(
            collection_url=collection_url,
            rerank_model=rerank_model,
            retriever_model=retriever_model,
            collection_name="test",
            cfg=solr_cfg
        )

        index_client.index_data(documents, soft_commit=True)
        search_result = search_client.semantic_search("web development project")
        cfg = GroqConfig()
        groq_obj = AsyncGroq(api_key=cfg.API_TOKEN)
        service_obj = CreateDocumentationContentService(groq_client=groq_obj, groq_config=cfg)
        result = await service_obj.create_document_content_from_messages(search_result, "test")
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert "Overview" in "".join(result)
        assert "Technical Requirements" in "".join(result)
        assert "https://discord.com/channels/test/1/" in "".join(result)
