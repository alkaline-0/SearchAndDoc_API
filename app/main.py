from contextlib import asynccontextmanager

import torch
import uvicorn
from fastapi import FastAPI

from db.config.solr_config import SolrConfig
from db.utils.sentence_transformer import STSentenceTransformer
from routers import create_collection_router, create_document_router, index_data_router
from services.config.config import MachineLearningModelConfig

config = {}
device = "mps" if torch.backends.mps.is_available() else "cpu"


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = SolrConfig()
    config["RERANK_MODEL"] = STSentenceTransformer(cfg.RERANK_MODEL_NAME, device=device)
    config["RETRIEVER_MODEL"] = STSentenceTransformer(
        cfg.RETRIEVER_MODEL_NAME, device=device
    )
    config["solr_config"] = cfg
    config["ml_config"] = MachineLearningModelConfig()

    yield

    config.clear()


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.state.config = config

    # routers
    app.include_router(index_data_router.router)
    app.include_router(create_collection_router.router)
    app.include_router(create_document_router.router)

    return app


if __name__ == "__main__":
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
