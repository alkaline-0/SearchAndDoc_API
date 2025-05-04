from collections.abc import Iterator

import fixtup
import pytest
import ray

from db.services.connection_factory_service import ConnectionFactoryService
from db.services.interfaces.connection_factory_service_interface import (
    ConnectionFactoryServiceInterface,
)
from db.utils.sentence_transformer import STSentenceTransformer
from tests.db.mocks.mock_solr_config import MockSolrConfig
from utils.get_logger import get_logger

if not ray.is_initialized():
    ray.init()


@pytest.fixture
def rerank_model():
    # Initialize the model
    return STSentenceTransformer(MockSolrConfig().RERANK_MODEL_NAME, device="mps")


@pytest.fixture()
def retriever_model():
    return STSentenceTransformer(MockSolrConfig().RETRIEVER_MODEL_NAME, device="mps")


@pytest.fixture(autouse=True)
def solr_conn_factory_obj() -> Iterator[ConnectionFactoryServiceInterface]:
    with fixtup.up("solr"):
        solr_conn = ConnectionFactoryService(MockSolrConfig(), logger=get_logger())
        yield solr_conn
        solr_conn.get_admin_client().delete_all_collections()
