from __future__ import annotations

from typing import Any

import pysolr

from db.data_access.interfaces.pysolr_interface import SolrClientInterface


class PysolrClient(SolrClientInterface):
    def __init__(self, **kwargs) -> any:
        self._solr = pysolr.Solr(**kwargs)

    def add(self, documents: list[dict[str, Any]], soft_commit: bool = True) -> any:
        self._solr.add(documents, softCommit=soft_commit)

    def search(self, *args, **kwargs) -> any:
        return self._solr.search(*args, **kwargs)
