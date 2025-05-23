from logging import Logger
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from db.utils.exceptions import SolrError
from services.create_collection_service import (
    CreateCollectionServiceParams,
    create_collection_service,
)
from services.index_data_service import IndexDataServiceParams, index_data_service
from utils.get_logger import get_logger

router = APIRouter(tags=["collections"])


class CreatecollectionRequest(BaseModel):
    server_id: Annotated[str, Field(min_length=1, max_length=20)]
    shards: int = Field(1, ge=1)
    replicas: int = Field(1, ge=1)


class IndexDataRequest(BaseModel):
    data: Annotated[list[dict], Field(min_length=1)]


@router.post("/collections")
async def create_collection(
    request: Request,
    payload: CreatecollectionRequest,
    logger: Annotated[Logger, Depends(get_logger)],
):
    try:
        solr_config = request.app.state.config.get("solr_config")
        payload_params = CreateCollectionServiceParams(
            server_id=payload.server_id,
            shards=payload.shards,
            replicas=payload.replicas,
            logger=logger,
            cfg=solr_config,
        )
        success = create_collection_service(params=payload_params)
        if not success:
            logger.error(f"Collection already exists {payload.server_id}.")
            raise HTTPException(status_code=400, detail="Collection already exists")

        logger.info(f"Created collection {payload.server_id} successfully.")
        return JSONResponse(
            content={"message": f"Collection {payload.server_id} created"},
            status_code=201,
        )
    except SolrError as e:
        logger.error(f"Failed to create collection: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/collections/{collection_id}")
async def index_data(
    collection_id: int,
    request: Request,
    payload: IndexDataRequest,
    logger: Annotated[Logger, Depends(get_logger)],
):
    try:
        request_params = IndexDataServiceParams(
            server_id=str(collection_id),
            data=payload.data,
            logger=logger,
            retriever_model=request.app.state.config["RETRIEVER_MODEL"],
            cfg=request.app.state.config["solr_config"],
        )

        success = index_data_service(params=request_params)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found"
            )

        return {"status": "success"}

    except SolrError as e:
        logger.error(f"Indexing failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
