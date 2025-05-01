import pytest

from db.solr_utils.solr_exceptions import SolrValidationError
from models.indexing_collection_model import IndexingCollectionModel
from models.semantic_search_model import SemanticSearchModel
from tests.db.mocks.mock_solr_config import MockSolrConfig
from tests.fixtures.test_data.fake_messages import documents


class TestSolrIndexingCollectionModel:

    def test_index_data_soft_commit_successfully(
        self, solr_collection_model, retriever_model, rerank_model
    ):
        collection_url = solr_collection_model.create_collection(
            collection_name="test_collection"
        )
        indexing_model = IndexingCollectionModel(
            cfg=MockSolrConfig(),
            collection_url=collection_url,
            retriever_model=retriever_model,
        )

        semantic_search_model = SemanticSearchModel(
            cfg=MockSolrConfig(),
            collection_url=collection_url,
            collection_name="test_collection",
            retriever_model=retriever_model,
            rerank_model=rerank_model,
        )
        indexing_model.index_data(documents, soft_commit=True)

        res = semantic_search_model.retrieve_all_docs()

        assert res is not None
        assert len(res) == len(documents)

    def test_index_data_hard_commit_successfully(
        self, solr_collection_model, retriever_model, rerank_model
    ):
        collection_url = solr_collection_model.create_collection(
            collection_name="test_collection"
        )
        indexing_model = IndexingCollectionModel(
            cfg=MockSolrConfig(),
            collection_url=collection_url,
            retriever_model=retriever_model,
        )

        semantic_search_model = SemanticSearchModel(
            cfg=MockSolrConfig(),
            collection_url=collection_url,
            collection_name="test_collection",
            retriever_model=retriever_model,
            rerank_model=rerank_model,
        )
        indexing_model.index_data(documents, soft_commit=False)

        res = semantic_search_model.retrieve_all_docs()

        assert res is not None
        assert len(res) == len(documents)

    def test_index_data_empty_data(self, solr_collection_model, retriever_model):
        with pytest.raises(SolrValidationError) as exec_info:
            collection_url = solr_collection_model.create_collection(
                collection_name="test_collection"
            )
            indexing_model = IndexingCollectionModel(
                cfg=MockSolrConfig(),
                collection_url=collection_url,
                retriever_model=retriever_model,
            )
            indexing_model.index_data([], soft_commit=True)
        assert "Data to index cannot be empty" in str(exec_info.value)
