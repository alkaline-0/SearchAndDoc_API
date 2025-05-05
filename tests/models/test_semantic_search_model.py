from unittest.mock import call, patch

import pytest

from db.utils.exceptions import SolrValidationError
from models.indexing_collection_model import IndexingCollectionModel
from models.semantic_search_model import SemanticSearchModel
from models.solr_collection_model import SolrCollectionModel
from tests.fixtures.test_data.fake_messages import documents
from utils.get_logger import get_logger


class TestSemanticSearchModel:
    logger = get_logger()

    def test_successful_semantic_search(
        self, solr_conn_factory_obj, retriever_model, rerank_model
    ):
        collection_admin_obj = SolrCollectionModel(
            logger=self.logger,
            collection_admin_service_obj=solr_conn_factory_obj.get_admin_client(),
        )
        collection_url = collection_admin_obj.create_collection("test_collection")
        IndexingCollectionModel(
            logger=self.logger,
            indexing_service_obj=solr_conn_factory_obj.get_index_client(
                retriever_model=retriever_model, collection_url=collection_url
            ),
        ).index_data(documents=documents, soft_commit=True)

        semantic_search_model = SemanticSearchModel(
            logger=self.logger,
            semantic_search_service_obj=solr_conn_factory_obj.get_search_client(
                collection_name="test_collection",
                collection_url=collection_url,
                rerank_model=rerank_model,
                retriever_model=retriever_model,
            ),
        )
        res = semantic_search_model.semantic_search(q="web backend implementation")

        assert res is not None
        assert len(res[0]["message_content"]) > 0

    def test_unsuccesful_search_due_to_invalid_query(
        self, solr_conn_factory_obj, retriever_model, rerank_model
    ):
        with pytest.raises(SolrValidationError) as excinfo:
            collection_admin_obj = SolrCollectionModel(
                logger=self.logger,
                collection_admin_service_obj=solr_conn_factory_obj.get_admin_client(),
            )
            collection_url = collection_admin_obj.create_collection("test_collection")
            IndexingCollectionModel(
                logger=self.logger,
                indexing_service_obj=solr_conn_factory_obj.get_index_client(
                    retriever_model=retriever_model, collection_url=collection_url
                ),
            ).index_data(documents=documents, soft_commit=True)

            semantic_search_model = SemanticSearchModel(
                logger=self.logger,
                semantic_search_service_obj=solr_conn_factory_obj.get_search_client(
                    collection_name="test_collection",
                    collection_url=collection_url,
                    rerank_model=rerank_model,
                    retriever_model=retriever_model,
                ),
            )
            with patch.object(semantic_search_model, "_logger") as mock_logger:
                semantic_search_model.semantic_search(" ")
        mock_logger.error.assert_has_calls([call(f"Invalid Search query:  ")])
        assert "Search query must be at least 4 letters" in str(excinfo.value)

    def test_unsuccesful_search_due_to_numbers_query(
        self, solr_conn_factory_obj, retriever_model, rerank_model
    ):
        """Test unsuccessful collection existence check due to wrong password."""
        with pytest.raises(SolrValidationError) as excinfo:
            collection_admin_obj = SolrCollectionModel(
                logger=self.logger,
                collection_admin_service_obj=solr_conn_factory_obj.get_admin_client(),
            )
            collection_url = collection_admin_obj.create_collection("test_collection")
            indexing_model = IndexingCollectionModel(
                logger=self.logger,
                indexing_service_obj=solr_conn_factory_obj.get_index_client(
                    retriever_model=retriever_model, collection_url=collection_url
                ),
            ).index_data(documents=documents, soft_commit=True)

            semantic_search_model = SemanticSearchModel(
                logger=self.logger,
                semantic_search_service_obj=solr_conn_factory_obj.get_search_client(
                    collection_name="test_collection",
                    collection_url=collection_url,
                    rerank_model=rerank_model,
                    retriever_model=retriever_model,
                ),
            )
            with patch.object(semantic_search_model, "_logger") as mock_logger:
                semantic_search_model.semantic_search("123testback")
            mock_logger.error.assert_has_calls(
                [call(f"Invalid Search query containing numbers 123testback")]
            )
        assert "Search query must be only english letters" in str(excinfo.value)

    def test_empty_query_semantic_search(
        self, solr_conn_factory_obj, retriever_model, rerank_model
    ):
        with pytest.raises(SolrValidationError) as exec_info:
            collection_admin_obj = SolrCollectionModel(
                logger=self.logger,
                collection_admin_service_obj=solr_conn_factory_obj.get_admin_client(),
            )
            collection_url = collection_admin_obj.create_collection("test_collection")
            IndexingCollectionModel(
                logger=self.logger,
                indexing_service_obj=solr_conn_factory_obj.get_index_client(
                    retriever_model=retriever_model, collection_url=collection_url
                ),
            ).index_data(documents=documents, soft_commit=True)

            semantic_search_model = SemanticSearchModel(
                logger=self.logger,
                semantic_search_service_obj=solr_conn_factory_obj.get_search_client(
                    collection_name="test_collection",
                    collection_url=collection_url,
                    rerank_model=rerank_model,
                    retriever_model=retriever_model,
                ),
            )
            with patch.object(semantic_search_model, "_logger") as mock_logger:
                semantic_search_model.semantic_search(q="")
            mock_logger.error.assert_has_calls([call(f"Invalid Search query: ")])
        assert "Search query must be at least 4 letters" in str(exec_info.value)
