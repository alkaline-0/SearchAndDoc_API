import datetime
from logging import Logger

from fastapi import HTTPException

from db.config.solr_config import SolrConfig
from db.services.connection_factory_service import ConnectionFactoryService
from db.utils.interfaces.sentence_transformer_interface import (
    SentenceTransformerInterface,
)
from models.semantic_search_model import SemanticSearchModel
from models.solr_collection_model import SolrCollectionModel
from services.config.config import MachineLearningModelConfig
from utils.machine_learning_model import AsyncGroqModel


async def create_document_service(
    server_id: str,
    logger: Logger,
    topic: str,
    retriever_model: SentenceTransformerInterface,
    rerank_model: SentenceTransformerInterface,
    start_date: datetime = None,
    end_date: datetime = None,
) -> str | None:
    cfg = SolrConfig()
    connection_obj = ConnectionFactoryService(cfg=cfg, logger=logger)
    collection_admin_service_obj = connection_obj.get_admin_client()

    collection_model = SolrCollectionModel(
        collection_name=server_id,
        collection_admin_service_obj=collection_admin_service_obj,
        logger=logger,
    )

    if not collection_model.collection_exist(server_id):
        logger.error(f"Collection {server_id} does not exist.")
        return None

    logger.info(f"Found collection {server_id}")
    collection_url = collection_model.get_collection_url()

    semantic_search_service = connection_obj.get_search_client(
        collection_name=server_id,
        retriever_model=retriever_model,
        rerank_model=rerank_model,
        collection_url=collection_url,
    )
    semantic_search_model = SemanticSearchModel(
        logger=logger,
        semantic_search_service_obj=semantic_search_service,
    )

    try:
        search_result = semantic_search_model.semantic_search(
            q=topic, start_date=start_date, end_date=end_date
        )
        logger.info(f"Retrieved {len(search_result)} documents")
    except Exception as e:
        logger.error(f"Search failed: {str(e)}", exc_info=True)
        raise HTTPException(500, "Search failed")

    if not search_result:
        logger.error("No documents found")
        return None

    try:
        ml_cfg = MachineLearningModelConfig()
        async with AsyncGroqModel(ml_cfg) as ml_model:
            content = await ml_model.create(messages=search_result, logger=logger)
        logger.info("Document content created successfully")
        return content
    except Exception as e:
        logger.error(f"Content generation failed: {str(e)}", exc_info=True)
        raise HTTPException(500, "Content generation failed")
