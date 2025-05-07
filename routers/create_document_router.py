from datetime import datetime
from logging import Logger
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from services.create_document_service import create_document_service
from utils.get_logger import get_logger

router = APIRouter(tags=["create-document"])


class CreateDocumentRequest(BaseModel):
    server_id: Annotated[str, Field(min_length=1, max_length=18)]
    topic: Annotated[str, Field(min_length=1, max_length=18)]
    start_date: str
    end_date: str


class CreateDocumentResponse(BaseModel):
    generated_document: str


@router.post("/create-document", response_model=CreateDocumentResponse)
async def create_document(
    request: Request,
    payload: CreateDocumentRequest,
    logger: Annotated[Logger, Depends(get_logger)],
):
    try:
        # Validate models exist
        retriever_model = request.app.state.ml_models.get("RETRIEVER_MODEL")
        rerank_model = request.app.state.ml_models.get("RERANK_MODEL")
        if not retriever_model or not rerank_model:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Models not initialized",
            )

        result = await create_document_service(
            server_id=payload.server_id,
            topic=payload.topic,
            logger=logger,
            retriever_model=retriever_model,
            rerank_model=rerank_model,
            start_date=datetime(payload.start_date),
            end_date=datetime(payload.end_date),
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create document. Invalid input or server error.",
            )
        return {"generated_document": result}

    except HTTPException as e:
        logger.error(f"Client error: {str(e)}", exc_info=True)
        raise

    except Exception as e:
        logger.error(f"Server error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
