from collections.abc import Iterator

import fixtup
import pytest
import ray

from db.helpers.sentence_transformer_impl import STSentenceTransformer
from db.solr_service_layers.solr_connection import SolrConnection
from models.solr_collection_model import SolrCollectionModel
from tests.db.mocks.mock_solr_config import MockSolrConfig

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
def solr_connection() -> Iterator[SolrConnection]:
    with fixtup.up("solr"):
        solr_conn = SolrConnection(MockSolrConfig())
        yield solr_conn
        solr_conn.get_admin_client().delete_all_collections()


@pytest.fixture(autouse=True)
def solr_collection_model() -> Iterator[SolrConnection]:
    solr_conn = SolrCollectionModel(MockSolrConfig())
    yield solr_conn
    solr_conn.delete_all_collections()
