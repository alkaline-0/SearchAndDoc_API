from datetime import datetime
from logging import Logger
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from db.utils.exceptions import SolrError
from services.create_document_service import (
    CreateDocumentServiceParams,
    create_document_service,
)
from utils.get_logger import get_logger

router = APIRouter(tags=["documents"])


class CreateDocumentRequest(BaseModel):
    server_id: Annotated[str, Field(min_length=1, max_length=18)]
    channel_id: int
    topic: Annotated[str, Field(min_length=1, max_length=35)]
    start_date: str
    end_date: str


class CreateDocumentResponse(BaseModel):
    generated_document: str


@router.post("/documents", response_model=CreateDocumentResponse)
async def create_document(
    request: Request,
    payload: CreateDocumentRequest,
    logger: Annotated[Logger, Depends(get_logger)],
):
    try:
        # Validate models exist
        retriever_model = request.app.state.config.get("RETRIEVER_MODEL")
        rerank_model = request.app.state.config.get("RERANK_MODEL")
        if not retriever_model or not rerank_model:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Models not initialized",
            )
        solr_date_format = "%Y-%m-%dT%H:%M:%SZ"
        request_params = CreateDocumentServiceParams(
            server_id=payload.server_id,
            topic=payload.topic,
            logger=logger,
            channel_id=payload.channel_id,
            retriever_model=retriever_model,
            rerank_model=rerank_model,
            start_date=datetime.strptime(payload.start_date, solr_date_format),
            end_date=datetime.strptime(payload.end_date, solr_date_format),
            cfg=request.app.state.config.get("solr_config"),
            ml_cfg=request.app.state.config.get("ml_config"),
        )

        result = await create_document_service(params=request_params)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create document. Invalid input or server error.",
            )
        return {"generated_document": result}

    except SolrError as e:
        logger.error(f"Server error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
