from abc import ABC

from db.solr_service_layers.interfaces.solr_connection_interface import SolrConnectionInterface
from db.solr_service_layers.solr_connection import SolrConnection
from db.solr_utils.solr_config import SolrConfig


class BaseModel(ABC):
  solr_conn_obj: SolrConnectionInterface = None
  cfg: SolrConfig = None
  
  def __init__(self, cfg: SolrConfig, solrConnection: SolrConnectionInterface):    
    self.cfg = cfg
    self.solr_conn_obj = solrConnection
