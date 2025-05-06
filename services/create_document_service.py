import datetime
from logging import Logger

from attr import dataclass
from fastapi import HTTPException

from db.config.solr_config import SolrConfig
from db.services.connection_factory_service import ConnectionFactoryService
from db.utils.interfaces.sentence_transformer_interface import (
    SentenceTransformerInterface,
)
from models.semantic_search_model import SemanticSearchModel
from models.solr_collection_model import SolrCollectionModel
from services.config.config import MachineLearningModelConfig
from services.create_collection_service import CreateCollectionServiceParams
from utils.machine_learning_model import AsyncGroqModel


@dataclass
class CreateDocumentServiceParams:
    server_id: str
    logger: Logger
    topic: str
    retriever_model: SentenceTransformerInterface
    rerank_model: SentenceTransformerInterface
    cfg: SolrConfig
    start_date: datetime = None
    end_date: datetime = None
    ml_cfg: MachineLearningModelConfig


async def create_document_service(params: CreateCollectionServiceParams) -> str | None:
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
            q=params.topic, start_date=params.start_date, end_date=params.end_date
        )
        params.logger.info(f"Retrieved {len(search_result)} documents")
    except Exception as e:
        params.logger.error(f"Search failed: {str(e)}", exc_info=True)
        raise HTTPException(500, "Search failed")

    if not search_result:
        params.logger.error("No documents found")
        return None

    try:
        async with AsyncGroqModel(params.ml_cfg) as ml_model:
            content = await ml_model.create(
                messages=search_result, logger=params.logger
            )
        params.logger.info("Document content created successfully")
        return content
    except Exception as e:
        params.logger.error(f"Content generation failed: {str(e)}", exc_info=True)
        raise HTTPException(500, "Content generation failed")
