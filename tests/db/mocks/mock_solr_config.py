import os

from attr import dataclass

from db.solr_utils.solr_exceptions import SolrValidationError


@dataclass
class MockSolrConfig:
    USER_NAME: str = None
    PASSWORD: str = None
    SOLR_HOST: str = None
    SOLR_PORT: str = None
    BASE_URL: str = None
    RETRIEVER_MODEL_NAME: str = "sentence-transformers/multi-qa-mpnet-base-dot-v1"
    RERANK_MODEL_NAME: str = "sentence-transformers/all-mpnet-base-v2"
    THRESHOLD: float = 0.2

    def __post_init__(self) -> None:
        self.USER_NAME = os.getenv("USER_NAME")
        self.PASSWORD = os.getenv("PASSWORD")
        self.SOLR_HOST = os.getenv("SOLR_HOST_TEST")
        self.SOLR_PORT = os.getenv("SOLR_PORT_TEST")
        if not all([self.USER_NAME, self.PASSWORD, self.SOLR_HOST, self.SOLR_PORT]):
            raise SolrValidationError(
                "Missing Solr configuration environment variables"
            )
        self.BASE_URL = f"http://{self.SOLR_HOST}:{self.SOLR_PORT}/solr/"

@dataclass
class MockSolrConfigWrongPassword(MockSolrConfig):
    def __post_init__(self) -> None:
        super().__post_init__()
        self.PASSWORD = "wrong_password"