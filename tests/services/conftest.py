from collections.abc import Iterator

import fixtup
import pytest
import ray

from db.services.connection import ConnectionFactory
from db.utils.sentence_transformer import STSentenceTransformer
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
def solr_collection_model() -> Iterator[ConnectionFactory]:
    with fixtup.up("solr"):
        solr_conn = SolrCollectionModel(MockSolrConfig())
        yield solr_conn
        solr_conn.delete_all_collections()
