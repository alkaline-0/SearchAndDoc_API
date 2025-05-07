from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from db.config.solr_config import SolrConfig
from db.utils.sentence_transformer import STSentenceTransformer
from routers import create_collection_router, create_document_router, index_data_router

ml_models = {}
config = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = SolrConfig()
    ml_models["RERANK_MODEL"] = STSentenceTransformer(
        cfg.RERANK_MODEL_NAME, device="mps"
    )
    ml_models["RETRIEVER_MODEL"] = STSentenceTransformer(
        cfg.RETRIEVER_MODEL_NAME, device="mps"
    )
    config["solr_config"] = SolrConfig()

    yield

    ml_models.clear()


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.state.ml_models = ml_models
    app.state.config = config

    # routers
    app.include_router(index_data_router.router)
    app.include_router(create_collection_router.router)
    app.include_router(create_document_router.router)

    return app


if __name__ == "__main__":
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
