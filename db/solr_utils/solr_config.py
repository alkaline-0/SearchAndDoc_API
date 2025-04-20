import os

from attr import dataclass



@dataclass
class SolrConfig:
    USER_NAME: str = None
    PASSWORD: str = None
    SOLR_HOST: str = None
    SOLR_PORT: str = None
    BASE_URL: str = None
    RETRIEVER_MODEL: str = "sentence-transformers/multi-qa-mpnet-base-dot-v1"
    RERANK_MODEL: str = "sentence-transformers/all-mpnet-base-v2"
    THRESHOLD: float = 0.2

    def __post_init__(self):
        self.USER_NAME = os.getenv("USER_NAME")
        self.PASSWORD = os.getenv("PASSWORD")
        self.SOLR_HOST = os.getenv("SOLR_HOST")
        self.SOLR_PORT = os.getenv("SOLR_PORT")
        if not all([self.USER_NAME, self.PASSWORD, self.SOLR_HOST, self.SOLR_PORT]):
            raise ValueError("Missing Solr configuration environment variables")
        self.BASE_URL = f"http://{self.USER_NAME}:{self.PASSWORD}@{self.SOLR_HOST}:{self.SOLR_PORT}/solr/"


