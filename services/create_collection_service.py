from logging import Logger

from attr import dataclass

from db.config.solr_config import SolrConfig
from db.infrastructure.connection_factory_service import ConnectionFactoryService
from models.solr_collection_model import SolrCollectionModel


@dataclass
class CreateCollectionServiceParams:
    server_id: str
    shards: int
    replicas: int
    logger: Logger
    cfg: SolrConfig


def create_collection_service(params: CreateCollectionServiceParams) -> bool:
    connection_obj = ConnectionFactoryService(cfg=params.cfg, logger=params.logger)
    collection_admin_service_obj = connection_obj.get_admin_client()

    collection_model = SolrCollectionModel(
        collection_name=params.server_id,
        collection_admin_service_obj=collection_admin_service_obj,
        logger=params.logger,
    )

    if collection_model.collection_exist():
        params.logger.error(f"Collection {params.server_id} already exists.")
        return False

    try:
        collection_model.create_collection(
            num_shards=params.shards, replicas_count=params.replicas
        )
        params.logger.info(
            f"Created collection {params.server_id} with {params.shards} shards and {params.replicas} replicas."
        )
        return True
    except Exception as e:
        params.logger.error(
            f"Failed to create collection: {str(e)}", exc_info=True, stack_info=True
        )
        raise
