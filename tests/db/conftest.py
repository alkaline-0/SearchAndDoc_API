from collections.abc import Iterator

import fixtup
import pytest

from db.helpers.sentence_transformer_impl import STSentenceTransformer
from db.solr_service_layers.solr_connection import SolrConnection
from tests.db.mocks.mock_solr_config import MockSolrConfig

cfg = MockSolrConfig()
RERANK_MODEL = STSentenceTransformer(cfg.RERANK_MODEL_NAME, device="mps")
RETRIEVER_MODEL = STSentenceTransformer(cfg.RETRIEVER_MODEL_NAME, device="mps")


@pytest.fixture(autouse=True)
def solr_client() -> Iterator[SolrConnection]:
    with fixtup.up("solr"):
        solr_conn = SolrConnection(cfg)

        yield solr_conn
        solr_conn.delete_all_collections()
