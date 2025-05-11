from __future__ import annotations

from typing import Any

import pysolr

from db.data_access.interfaces.pysolr_interface import SolrClientInterface


class PysolrClient(SolrClientInterface):
    def __init__(self, solr_url: str):
        self._solr = pysolr.Solr(solr_url)

    def add(self, documents: list[dict[str, Any]]):
        self._solr.add(documents)

    def commit(self, soft_commit: bool = True):
        self._solr.commit(softCommit=soft_commit)

    def search(self, *args, **kwargs):
        return self._solr.search(*args, **kwargs)
