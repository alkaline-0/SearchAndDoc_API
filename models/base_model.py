from db.config.solr_config import SolrConfig
from db.services.connection import ConnectionFactory


class BaseModel:
    cfg: SolrConfig = None

    def __init__(
        self,
    ) -> None:
        pass

    def get_connection_object(self, cfg: SolrConfig):
        return ConnectionFactory(cfg)
