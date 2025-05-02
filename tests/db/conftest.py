from collections.abc import Iterator

import fixtup
import pytest
import ray

from db.services.connection_factory_service import ConnectionFactoryService
from db.utils.sentence_transformer import STSentenceTransformer
from tests.db.mocks.mock_solr_config import MockSolrConfig

if not ray.is_initialized():
    ray.init()


@pytest.fixture
def rerank_model() -> STSentenceTransformer:
    # Initialize the model
    return STSentenceTransformer(MockSolrConfig().RERANK_MODEL_NAME, device="mps")


@pytest.fixture()
def retriever_model() -> STSentenceTransformer:
    return STSentenceTransformer(MockSolrConfig().RETRIEVER_MODEL_NAME, device="mps")


@pytest.fixture(autouse=True)
def solr_connection() -> Iterator[ConnectionFactoryService]:
    with fixtup.up("solr"):
        solr_conn = ConnectionFactoryService(MockSolrConfig())
        yield solr_conn
        solr_conn.get_admin_client().delete_all_collections()
