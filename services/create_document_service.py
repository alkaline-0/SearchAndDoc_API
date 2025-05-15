from datetime import datetime
from logging import Logger

from attr import dataclass
from fastapi import HTTPException
from ray import logger

from db.config.solr_config import SolrConfig
from db.infrastructure.connection_factory_service import ConnectionFactoryService
from db.utils.interfaces.sentence_transformer_interface import (
    SentenceTransformerInterface,
)
from models.semantic_search_model import SemanticSearchModel
from models.solr_collection_model import SolrCollectionModel
from services.config.config import MachineLearningModelConfig
from services.create_collection_service import CreateCollectionServiceParams
from services.create_documentation_content_service import (
    CreateDocumentationContentService,
)
from utils.machine_learning_model import AsyncGroqModel


@dataclass
class CreateDocumentServiceParams:
    server_id: str
    logger: Logger
    topic: str
    channel_id: int
    retriever_model: SentenceTransformerInterface
    rerank_model: SentenceTransformerInterface
    cfg: SolrConfig
    ml_cfg: MachineLearningModelConfig
    start_date: datetime = None
    end_date: datetime = None


async def create_document_service(params: CreateCollectionServiceParams) -> str:
    connection_obj = ConnectionFactoryService(cfg=params.cfg, logger=params.logger)
    collection_admin_service_obj = connection_obj.get_admin_client()

    collection_model = SolrCollectionModel(
        collection_name=params.server_id,
        collection_admin_service_obj=collection_admin_service_obj,
        logger=params.logger,
    )

    if not collection_model.collection_exist():
        params.logger.error(f"Collection {params.server_id} does not exist.")
        return None

    params.logger.info(f"Found collection {params.server_id}")
    collection_url = collection_model.get_collection_url()

    semantic_search_service = connection_obj.get_search_client(
        collection_name=params.server_id,
        retriever_model=params.retriever_model,
        rerank_model=params.rerank_model,
        collection_url=collection_url,
    )
    semantic_search_model = SemanticSearchModel(
        logger=params.logger,
        semantic_search_service_obj=semantic_search_service,
    )

    try:
        search_result = semantic_search_model.semantic_search(
            q=params.topic,
            channel_id=params.channel_id,
            start_date=params.start_date,
            end_date=params.end_date,
        )
        params.logger.info(f"Retrieved {len(search_result)} documents")
    except Exception as e:
        params.logger.error(f"Search failed: {str(e)}", exc_info=True)
        raise HTTPException(500, "Search failed")

    if not search_result:
        params.logger.error("No documents found")
        return None

    try:
        ml_client = AsyncGroqModel(params.ml_cfg)
        content_service = CreateDocumentationContentService(
            ml_client=ml_client, logger=logger
        )
        content = await content_service.create_document_content_from_messages(
            documents=search_result, server_id=params.server_id
        )

        params.logger.info("Document content created successfully")
        return content
    except Exception as e:
        params.logger.error(
            f"Content generation failed: {str(e)}", exc_info=True, stack_info=True
        )
        raise e
