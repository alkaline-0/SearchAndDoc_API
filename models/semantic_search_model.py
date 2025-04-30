from base_model import BaseModel

from db.helpers.interfaces.sentence_transformer_interface import \
    SentenceTransformerInterface
from db.solr_service_layers.interfaces.solr_connection_interface import \
    SolrConnectionInterface
from db.solr_service_layers.interfaces.solr_search_interface import \
    SolrSearchInterface
from db.solr_utils.solr_config import SolrConfig
from db.solr_utils.solr_exceptions import SolrValidationError


class SemanticSearchModel(BaseModel):
  _semantic_search_obj: SolrSearchInterface = None
  
  def __init__(self, cfg: SolrConfig, collection_name: str, solr_conn: SolrConnectionInterface, collection_url: str, retriever_model: SentenceTransformerInterface, rerank_model: SentenceTransformerInterface):
    super().__init__(cfg=cfg, solr_connection=solr_conn)
    
    self._semantic_search_obj = super().solr_conn_obj.get_search_client(collection_url=collection_url, rerank_model=rerank_model, retriever_model=retriever_model, collection_name= collection_name)
    
  def semantic_search(self, q: str, threshold: float = 0.1)->list[dict]:
    if not self._query_valid(q=q):
      raise

    return self._semantic_search_obj.semantic_search(q=q.lower(),threshold=threshold)
    
  def _query_valid(self, q:str) -> bool:
    if len(q) < 4:
      raise SolrValidationError("Search query must be at least 4 letters")
    
    if not q.isalpha():
      raise SolrValidationError("Search query must be only english letters")
    
  def retriece_all_docs(self)->list:
    return self._semantic_search_obj.retrieve_all_docs()