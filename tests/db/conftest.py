import os
from collections.abc import Iterator

import fixtup
import pytest

from db.solr import SolrCollectionAgent


@pytest.fixture(autouse=True)
def solr_test_agent() -> Iterator[SolrCollectionAgent]:
    with fixtup.up("solr"):
        client = SolrCollectionAgent(
            user_name=os.getenv("USER_NAME"),
            password=os.getenv("PASSWORD"),
            solr_host=os.getenv("SOLR_HOST_TEST"),
            solr_port=os.getenv("SOLR_PORT_TEST"),
            collection_name="test_collection",
        )
        yield client
        client.delete_all_collections()
