from unittest.mock import call, patch

import pytest

from db.utils.exceptions import SolrValidationError
from models.indexing_collection_model import IndexingCollectionModel
from models.semantic_search_model import SemanticSearchModel
from models.solr_collection_model import SolrCollectionModel
from tests.fixtures.test_data.fake_messages import documents
from utils.get_logger import get_logger


class TestSolrIndexingCollectionModel:
    logger = get_logger()

    def test_index_data_soft_commit_successfully(
        self, solr_conn_factory_obj, retriever_model, rerank_model
    ):
        collection_name = "test_collection"
        collection_admin_obj = SolrCollectionModel(
            collection_name=collection_name,
            logger=self.logger,
            collection_admin_service_obj=solr_conn_factory_obj.get_admin_client(),
        )
        collection_url = collection_admin_obj.create_collection()
        indexing_model = IndexingCollectionModel(
            logger=self.logger,
            indexing_service_obj=solr_conn_factory_obj.get_index_client(
                retriever_model=retriever_model, collection_url=collection_url
            ),
        )

        semantic_search_model = SemanticSearchModel(
            logger=self.logger,
            semantic_search_service_obj=solr_conn_factory_obj.get_search_client(
                collection_name=collection_name,
                collection_url=collection_url,
                rerank_model=rerank_model,
                retriever_model=retriever_model,
            ),
        )
        indexing_model.index_data(documents, soft_commit=True)

        rows_count = semantic_search_model.get_rows_count()
        assert rows_count == len(documents)

    def test_index_data_hard_commit_successfully(
        self, solr_conn_factory_obj, retriever_model, rerank_model
    ):
        collection_name = "test_collection"
        collection_admin_obj = SolrCollectionModel(
            collection_name=collection_name,
            logger=self.logger,
            collection_admin_service_obj=solr_conn_factory_obj.get_admin_client(),
        )
        collection_url = collection_admin_obj.create_collection()
        indexing_model = IndexingCollectionModel(
            logger=self.logger,
            indexing_service_obj=solr_conn_factory_obj.get_index_client(
                retriever_model=retriever_model, collection_url=collection_url
            ),
        )

        semantic_search_model = SemanticSearchModel(
            logger=self.logger,
            semantic_search_service_obj=solr_conn_factory_obj.get_search_client(
                collection_name=collection_name,
                collection_url=collection_url,
                rerank_model=rerank_model,
                retriever_model=retriever_model,
            ),
        )
        indexing_model.index_data(documents, soft_commit=False)

        rows_count = semantic_search_model.get_rows_count()
        assert rows_count == len(documents)

    def test_index_data_empty_data(self, solr_conn_factory_obj, retriever_model):
        with pytest.raises(SolrValidationError) as exec_info:

            collection_name = "test_collection"
            collection_admin_obj = SolrCollectionModel(
                collection_name=collection_name,
                logger=self.logger,
                collection_admin_service_obj=solr_conn_factory_obj.get_admin_client(),
            )
            collection_url = collection_admin_obj.create_collection()
            indexing_model = IndexingCollectionModel(
                logger=self.logger,
                indexing_service_obj=solr_conn_factory_obj.get_index_client(
                    retriever_model=retriever_model, collection_url=collection_url
                ),
            )
            with patch.object(indexing_model, "_logger") as mock_logger:
                indexing_model.index_data([], soft_commit=True)
        assert "Data to index cannot be empty" in str(exec_info.value)
        mock_logger.error.assert_has_calls(
            [call("failed to index documents because length is less than one")]
        )
