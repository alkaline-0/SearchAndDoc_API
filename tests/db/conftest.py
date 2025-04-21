from collections.abc import Iterator

import fixtup
import pytest

from db.solr_utils.solr_client import SolrCollectionClient
from db.solr_utils.solr_connection import SolrConnection
from tests.db.mocks.mock_solr_config import MockSolrConfig


@pytest.fixture(autouse=True)
def solr_test_agent() -> Iterator[SolrCollectionClient]:
    with fixtup.up("solr"):
        solr_conn = SolrConnection(cfg=MockSolrConfig())
        client = solr_conn.get_collection_client("test")
        yield client
        solr_conn.delete_all_collections()
