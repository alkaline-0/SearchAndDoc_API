from logging import Logger

from db.config.solr_config import SolrConfig
from db.services.connection_factory_service import ConnectionFactoryService
from models.solr_collection_model import SolrCollectionModel


def create_collection(
    server_id: str, shards: int, replicas: int, logger: Logger
) -> bool:
    cfg = SolrConfig()
    connection_obj = ConnectionFactoryService(cfg=cfg, logger=logger)
    collection_admin_service_obj = connection_obj.get_admin_client()

    collection_model = SolrCollectionModel(
        collection_name=server_id,
        collection_admin_service_obj=collection_admin_service_obj,
        logger=logger,
    )

    if collection_model.collection_exist(server_id):
        logger.error(f"Collection {server_id} already exists.")
        return False

    try:
        collection_model.create_collection(num_shards=shards, replicas_count=replicas)
        logger.info(
            f"Created collection {server_id} with {shards} shards and {replicas} replicas."
        )
        return True
    except Exception as e:
        logger.error(
            f"Failed to create collection: {str(e)}", exc_info=True, stack_info=True
        )
        raise
