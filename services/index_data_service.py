import multiprocessing

from attr import dataclass
from joblib import Logger

from db.config.solr_config import SolrConfig
from db.services.connection_factory_service import ConnectionFactoryService
from db.utils.interfaces.sentence_transformer_interface import (
    SentenceTransformerInterface,
)
from models.indexing_collection_model import IndexingCollectionModel
from models.solr_collection_model import SolrCollectionModel


@dataclass
class IndexDataServiceParams:
    server_id: str
    data: list[dict]
    logger: Logger
    retriever_model: SentenceTransformerInterface
    cfg: SolrConfig


def _index_data_worker(data: list[dict], collection_url: str, cfg_dict: dict):
    """Worker process that reinitializes dependencies from primitives"""
    # Reconstruct config from dictionary
    cfg = SolrConfig(**cfg_dict)

    # Recreate connections inside the worker
    connection_obj = ConnectionFactoryService(cfg=cfg)
    index_data_service_obj = connection_obj.get_index_client(
        collection_url=collection_url
    )
    index_data_model = IndexingCollectionModel(
        indexing_service_obj=index_data_service_obj
    )

    # Perform the actual indexing
    index_data_model.index_data(documents=data, soft_commit=False)


def index_data_service(params: IndexDataServiceParams) -> bool:
    connection_obj = ConnectionFactoryService(cfg=params.cfg, logger=params.logger)
    collection_admin_service_obj = connection_obj.get_admin_client()

    collection_model = SolrCollectionModel(
        collection_name=params.server_id,
        collection_admin_service_obj=collection_admin_service_obj,
        logger=params.logger,
    )

    if not collection_model.collection_exist():
        params.logger.error(f"Collection {params.server_id} does not exist.")
        return False

    params.logger.info(
        f"Found the collection {params.server_id}, proceeding with indexing"
    )

    collection_url = collection_model.get_collection_url()
    index_data_service_obj = connection_obj.get_index_client(
        collection_url=collection_url, retriever_model=params.retriever_model
    )
    index_data_model = IndexingCollectionModel(
        indexing_service_obj=index_data_service_obj, logger=params.logger
    )

    try:
        params.logger.info(
            "Indexing the data without storing in the hard driver for speed."
        )
        index_data_model.index_data(documents=params.data, soft_commit=True)

        params.logger.info(
            "soft commit indexing finished successfully, spawning a process to store to hard disk "
        )
        process = multiprocessing.Process(
            target=_index_data_worker,
            args=(params.data, collection_url, params.cfg.__dict__),
        )
        process.start()
        return True
    except Exception:
        params.logger.error(
            "Failed to index data in index data service", stack_info=True, exc_info=True
        )
        raise
