import os

from attr import dataclass


@dataclass
class SolrConfig:
    USER_NAME: str = os.getenv("USER_NAME")
    PASSWORD: str = os.getenv("PASSWORD")
    SOLR_HOST: str = os.getenv("SOLR_HOST")
    SOLR_PORT: str = os.getenv("SOLR_PORT")
    BASE_URL: str = f"http://{SOLR_HOST}:{SOLR_PORT}/solr/"

    RETRIEVER_MODEL_NAME: str = "sentence-transformers/multi-qa-mpnet-base-dot-v1"
    RERANK_MODEL_NAME: str = "sentence-transformers/all-mpnet-base-v2"
    THRESHOLD: float = 0.0
