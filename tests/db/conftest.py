import os
from collections.abc import Iterator

import fixtup
import pytest

from db.solr import Solr


@pytest.fixture(scope="session")
def solr_test_client() -> Iterator[Solr]:
    """Create a Solr test client fixture.

    Yields:
        Configured Solr client for testing
    """
    with fixtup.up("solr"):
        client = Solr(
            user_name=os.getenv("USER_NAME"),
            password=os.getenv("PASSWORD"),
            solr_host=os.getenv("SOLR_HOST_TEST"),
            solr_port=os.getenv("SOLR_PORT_TEST"),
        )
        yield client


@pytest.fixture(autouse=True)
def setup_and_teardown(solr_test_client):
    yield
    solr_test_client.delete_all_collections()
