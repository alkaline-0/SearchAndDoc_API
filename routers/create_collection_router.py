from logging import Logger
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from services.create_collection_service import create_collection_service
from utils.get_logger import get_logger

router = APIRouter(tags=["create_collection"])


class CreatecollectionRequest(BaseModel):
    server_id: Annotated[str, Field(min_length=1, max_length=18)]
    shards: int = Field(1, ge=1)
    replicas: int = Field(1, ge=1)


@router.post("/create-collection")
async def create_collection(
    request: CreatecollectionRequest, logger: Annotated[Logger, Depends(get_logger)]
):
    try:
        success = create_collection_service(
            server_id=request.server_id,
            shards=request.shards,
            replicas=request.replicas,
            logger=logger,
        )
        if not success:
            raise HTTPException(status_code=400, detail="Collection already exists")
        return JSONResponse(
            content={"message": f"Collection {request.server_id} created"},
            status_code=201,
        )
    except Exception as e:
        logger.error(f"Failed to create collection: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
