import datetime
from abc import ABC, abstractmethod
from logging import Logger

from attr import dataclass

from db.config.solr_config import SolrConfig
from db.data_access.interfaces.http_client_interface import SolrHttpClientInterface
from db.data_access.interfaces.pysolr_interface import SolrClientInterface
from db.utils.interfaces.rerank_strategy_interface import RerankStrategy
from db.utils.interfaces.retrieval_strategy_interface import RetrievalStrategy
from db.utils.interfaces.sentence_transformer_interface import (
    SentenceTransformerInterface,
)


@dataclass
class SemanticSearchServiceAttrs:
    logger: Logger
    solr_client: SolrClientInterface
    retriever_model: SentenceTransformerInterface
    rerank_model: SentenceTransformerInterface
    cfg: SolrConfig
    collection_name: str
    retriever_strategy: RetrievalStrategy
    reranker_strategy: RerankStrategy
    http_client: SolrHttpClientInterface


class SemanticSearchServiceInterface(ABC):
    """Interface for Solr connection and client creation."""

    @abstractmethod
    def __init__(self, logger: Logger = None):
        pass

    @abstractmethod
    def semantic_search(
        self,
        q: str,
        threshold: float,
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> list[dict]:
        pass
