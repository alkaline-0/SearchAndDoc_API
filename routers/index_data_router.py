from logging import Logger
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from services.index_data_service import index_data_service
from utils.get_logger import get_logger

router = APIRouter(tags=["index_data"])


class IndexDataRequest(BaseModel):
    server_id: Annotated[str, Field(min_length=1, max_length=18)]
    data: Annotated[list[dict], Field(min_length=1)]


@router.post("/index_data")
async def index_data(
    request: Request,
    payload: IndexDataRequest,
    logger: Annotated[Logger, Depends(get_logger)],
):
    try:
        success = index_data_service(
            server_id=payload.server_id,
            data=payload.data,
            logger=logger,
            retriever_model=request.app.state.ml_models["RETRIEVER_MODEL"],
        )

        if not success:
            return RedirectResponse(
                url=f"/create-collection?server_id={payload.server_id}",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Indexing failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
