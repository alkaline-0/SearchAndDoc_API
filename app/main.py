from contextlib import asynccontextmanager

import torch
import uvicorn
from fastapi import FastAPI

from db.config.solr_config import SolrConfig
from db.utils.sentence_transformer import STSentenceTransformer
from routers import collections, documents
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
    app.include_router(collections.router)
    app.include_router(documents.router)

    return app


if __name__ == "__main__":
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
