from typing import Any, List
import pysolr
from sentence_transformers import SentenceTransformer

from db.solr_utils.pysolr_interface import SolrClientInterface

class PysolrClient(SolrClientInterface):
    def __init__(self, solr_url: str):
        self._solr = pysolr.Solr(solr_url)

    def add(self, documents: List[dict[str, Any]]):
        self._solr.add(documents)

    def commit(self, softCommit: bool = True):
        self._solr.commit(softCommit=softCommit)

    def search(self, *args, **kwargs):
        return self._solr.search(*args, **kwargs)