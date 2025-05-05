import multiprocessing
from joblib import Logger
from db.config.solr_config import SolrConfig
from db.services.connection_factory_service import ConnectionFactoryService
from db.utils.interfaces.sentence_transformer_interface import SentenceTransformerInterface
from models.indexing_collection_model import IndexingCollectionModel
from models.solr_collection_model import SolrCollectionModel


def index_data_service(server_id: str, data: list[dict], logger: Logger, retriever_model: SentenceTransformerInterface)->bool:
  cfg = SolrConfig()
  connection_obj = ConnectionFactoryService(cfg=cfg, logger=logger)
  collection_admin_service_obj=connection_obj.get_admin_client()
  
  collection_model = SolrCollectionModel(collection_name=server_id,collection_admin_service_obj=collection_admin_service_obj
                                         , logger=logger)
  
  if not collection_model.collection_exist(server_id):
    logger.error(f"Collection {server_id} does not exist.")
    return False
  
  logger.info(f"Found the collection {server_id}, proceeding with indexing")
  
  collection_url = collection_model.get_collection_url()
  index_data_service_obj = connection_obj.get_index_client(collection_url=collection_url, retriever_model=retriever_model)
  index_data_model = IndexingCollectionModel(indexing_service_obj=index_data_service_obj, logger=logger)
  
  try:
    logger.info("Indexing the data without storing in the hard driver for speed.")
    index_data_model.index_data(documents=data, soft_commit=True)
    
    logger.info("soft commit indexing finished successfully, spawning a process to store to hard disk ")
    process = multiprocessing.Process(
            target=index_data_model.index_data,
            args=(data, False)
        )
    process.start()
    return True
  except Exception as e:
    logger.error(e,stack_info=True, exc_info=True)
    raise 
  