from logging import Logger
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from db.utils.exceptions import SolrError
from services.index_data_service import IndexDataServiceParams, index_data_service
from utils.get_logger import get_logger

router = APIRouter(tags=["index_data"])


class IndexDataRequest(BaseModel):
    server_id: Annotated[str, Field(min_length=1, max_length=18)]
    data: Annotated[list[dict], Field(min_length=1)]


@router.post("/index-data")
async def index_data(
    request: Request,
    payload: IndexDataRequest,
    logger: Annotated[Logger, Depends(get_logger)],
):
    try:
        request_params = IndexDataServiceParams(
            server_id=payload.server_id,
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
