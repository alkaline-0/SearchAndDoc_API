import os

from attr import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class MockSolrConfig:
    USER_NAME: str = os.getenv("USER_NAME")
    PASSWORD: str = os.getenv("PASSWORD")
    SOLR_HOST: str = os.getenv("SOLR_HOST_TEST")
    SOLR_PORT: str = os.getenv("SOLR_PORT_TEST")
    BASE_URL: str = f"http://{SOLR_HOST}:{SOLR_PORT}/solr/"

    RETRIEVER_MODEL_NAME: str = "sentence-transformers/multi-qa-mpnet-base-dot-v1"
    RERANK_MODEL_NAME: str = "sentence-transformers/all-mpnet-base-v2"
    THRESHOLD: float = 0.2
