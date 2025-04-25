from collections.abc import Iterator

import fixtup
import pytest

from db.solr_service_layers.solr_connection import SolrConnection
from db.solr_service_layers.solr_index_collection_client import \
    SolrIndexCollectionClient
from tests.db.mocks.mock_solr_config import MockSolrConfig


@pytest.fixture(autouse=True)
def solr_client() -> Iterator[SolrIndexCollectionClient]:
    with fixtup.up("solr"):
        solr_conn = SolrConnection(cfg=MockSolrConfig())

        yield solr_conn
        solr_conn.delete_all_collections()
