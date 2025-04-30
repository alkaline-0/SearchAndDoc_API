from db.solr_service_layers import solr_admin
from db.solr_service_layers.interfaces.solr_admin_interface import SolrAdminInterface
from db.solr_service_layers.interfaces.solr_connection_interface import SolrConnectionInterface
from db.solr_service_layers.solr_admin import SolrAdminClient
from db.solr_utils.solr_config import SolrConfig
from db.solr_utils.solr_exceptions import SolrConnectionError, SolrValidationError
from models.base_model import BaseModel


class SolrCollectionModel(BaseModel):
  
  solr_admin_obj: SolrAdminInterface = None
  
  def __init__(self, cfg: SolrConfig, solr_conn_obj: SolrConnectionInterface):
    self._validate_credentials(cfg)    
    super().__init__(cfg=cfg, solrConnection=solr_conn_obj)
    
    self.solr_admin_obj = solr_conn_obj.get_admin_client()

  def create_new_collection(self, collection_name: str, num_shards: int = 10, replicas_count: int = 2)->str:
    if not collection_name:
            raise SolrValidationError("Collection name cannot be empty")
    if num_shards <= 0 or replicas_count <=0 :
            raise SolrValidationError("Number of shards and replicas count must be greater than 0")
    if self.collection_exist(collection_name):
          raise SolrConnectionError("Cannot create a collection with the same name as existing one")
        
    return self.solr_admin_obj.create_collection(
                collection_name=collection_name, num_shards=num_shards, replica_count=replicas_count)
            
  def delete_collections(self):
    return self.solr_admin_obj.delete_all_collections()
  
  def collection_exist(self, collection_name: str):
    return self.solr_admin_obj.collection_exist(collection_name=collection_name)
    
  def _validate_credentials(self, cfg):
    """Handles None, empty strings, and whitespace."""
    if cfg.USER_NAME is None or cfg.PASSWORD is None:
        raise SolrValidationError("Username/password cannot be None")

    if not cfg.USER_NAME.strip() or not cfg.PASSWORD.strip():
        raise SolrValidationError(
            "Username/password cannot be empty or whitespace-only"
        )