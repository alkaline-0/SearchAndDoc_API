from base_model import BaseModel
from db.helpers.interfaces.sentence_transformer_interface import SentenceTransformerInterface
from db.solr_service_layers.interfaces.solr_connection_interface import SolrConnectionInterface
from db.solr_service_layers.interfaces.solr_index_interface import SolrIndexInerface
from db.solr_service_layers.solr_index_collection_client import SolrIndexCollectionClient
from db.solr_utils.solr_exceptions import SolrValidationError


class IndexingCollectionModel(BaseModel):
  _indexing_client: SolrIndexInerface = None
  
  def __init__(self, cfg, solr_conn: SolrConnectionInterface, collection_url: str, retriever_model: SentenceTransformerInterface):
    super().__init__(cfg=cfg, solrConnection=solr_conn)
    self._indexing_client = super().solr_conn_obj.get_index_client(collection_url=collection_url, retriever_model=retriever_model)
    
  def index_data(self, documents: list[dict], soft_commit:bool = True)->None:
    if not len(documents):
      raise SolrValidationError("Data to index cannot be empty")
    
    self._indexing_client.index_data(data=documents, soft_commit=soft_commit)
    
  