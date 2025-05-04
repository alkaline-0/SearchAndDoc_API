import pytest

from db.utils.exceptions import SolrValidationError
from models.indexing_collection_model import IndexingCollectionModel
from models.semantic_search_model import SemanticSearchModel
from models.solr_collection_model import SolrCollectionModel
from tests.fixtures.test_data.fake_messages import documents


class TestSemanticSearchModel:
    def test_successful_semantic_search(
        self, solr_conn_factory_obj, retriever_model, rerank_model
    ):
        collection_admin_obj = SolrCollectionModel(
            collection_admin_service_obj=solr_conn_factory_obj.get_admin_client()
        )
        collection_url = collection_admin_obj.create_collection("test_collection")
        indexing_model = IndexingCollectionModel(
            indexing_service_obj=solr_conn_factory_obj.get_index_client(
                retriever_model=retriever_model, collection_url=collection_url
            )
        ).index_data(documents=documents, soft_commit=True)

        semantic_search_model = SemanticSearchModel(
            semantic_search_service_obj=solr_conn_factory_obj.get_search_client(
                collection_name="test_collection",
                collection_url=collection_url,
                rerank_model=rerank_model,
                retriever_model=retriever_model,
            )
        )
        res = semantic_search_model.semantic_search(q="web backend implementation")
        assert res is not None
        assert len(res[0]["message_content"]) > 0

    def test_unsuccesful_search_due_to_invalid_query(
        self, solr_conn_factory_obj, retriever_model, rerank_model
    ):
        with pytest.raises(SolrValidationError) as excinfo:
            collection_admin_obj = SolrCollectionModel(
                collection_admin_service_obj=solr_conn_factory_obj.get_admin_client()
            )
            collection_url = collection_admin_obj.create_collection("test_collection")
            IndexingCollectionModel(
                indexing_service_obj=solr_conn_factory_obj.get_index_client(
                    retriever_model=retriever_model, collection_url=collection_url
                )
            ).index_data(documents=documents, soft_commit=True)

            semantic_search_model = SemanticSearchModel(
                semantic_search_service_obj=solr_conn_factory_obj.get_search_client(
                    collection_name="test_collection",
                    collection_url=collection_url,
                    rerank_model=rerank_model,
                    retriever_model=retriever_model,
                )
            )
            semantic_search_model.semantic_search(" ")
        assert "Search query must be at least 4 letters" in str(excinfo.value)

    def test_unsuccesful_search_due_to_numbers_query(
        self, solr_conn_factory_obj, retriever_model, rerank_model
    ):
        """Test unsuccessful collection existence check due to wrong password."""
        with pytest.raises(SolrValidationError) as excinfo:
            collection_admin_obj = SolrCollectionModel(
                collection_admin_service_obj=solr_conn_factory_obj.get_admin_client()
            )
            collection_url = collection_admin_obj.create_collection("test_collection")
            indexing_model = IndexingCollectionModel(
                indexing_service_obj=solr_conn_factory_obj.get_index_client(
                    retriever_model=retriever_model, collection_url=collection_url
                )
            ).index_data(documents=documents, soft_commit=True)

            semantic_search_model = SemanticSearchModel(
                semantic_search_service_obj=solr_conn_factory_obj.get_search_client(
                    collection_name="test_collection",
                    collection_url=collection_url,
                    rerank_model=rerank_model,
                    retriever_model=retriever_model,
                )
            )
            semantic_search_model.semantic_search("123testback")
        assert "Search query must be only english letters" in str(excinfo.value)

    def test_empty_query_semantic_search(
        self, solr_conn_factory_obj, retriever_model, rerank_model
    ):
        with pytest.raises(SolrValidationError) as exec_info:
            collection_admin_obj = SolrCollectionModel(
                collection_admin_service_obj=solr_conn_factory_obj.get_admin_client()
            )
            collection_url = collection_admin_obj.create_collection("test_collection")
            indexing_model = IndexingCollectionModel(
                indexing_service_obj=solr_conn_factory_obj.get_index_client(
                    retriever_model=retriever_model, collection_url=collection_url
                )
            ).index_data(documents=documents, soft_commit=True)

            semantic_search_model = SemanticSearchModel(
                semantic_search_service_obj=solr_conn_factory_obj.get_search_client(
                    collection_name="test_collection",
                    collection_url=collection_url,
                    rerank_model=rerank_model,
                    retriever_model=retriever_model,
                )
            )
            semantic_search_model.semantic_search(q="")
        assert "Search query must be at least 4 letters" in str(exec_info.value)
