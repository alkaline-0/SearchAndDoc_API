from db.solr_service_layers.solr_connection import SolrConnection
from db.solr_utils.solr_config import SolrConfig


class BaseModel:
    cfg: SolrConfig = None

    def __init__(
        self,
    ) -> None:
        pass

    def get_connection_object(self, cfg: SolrConfig):
        return SolrConnection(cfg)
