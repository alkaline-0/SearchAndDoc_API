from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from db.data_access.solr_http_client import SolrHttpClient
from routers.collections import CreatecollectionRequest, IndexDataRequest
from tests.db.mocks.mock_solr_config import MockSolrConfig
from tests.fixtures.test_data.fake_messages import documents
from utils.get_logger import get_logger


class TestIndexDataRouter:
    @pytest.mark.asyncio
    async def test_index_data_successfully(self, solr_connection):
        app = create_app()
        with TestClient(app) as test_router:
            request_params = CreatecollectionRequest(
                server_id="5678", shards=1, replicas=1
            )
            mock_cfg = MockSolrConfig()
            with patch.dict(
                test_router.app.state.config, {"solr_config": MockSolrConfig()}
            ):
                test_router.post(
                    "/collections", content=request_params.model_dump_json()
                )
                index_data_request = IndexDataRequest(data=documents)
                response = test_router.post(
                    "/collections/5678", content=index_data_request.model_dump_json()
                )

            assert response.status_code == 200
            http_client = SolrHttpClient(cfg=MockSolrConfig(), logger=get_logger())
            rows_count_resp = http_client.send_request(
                url=f"{mock_cfg.BASE_URL}5678/select?indent=on&q=*:*&wt=json&rows=0",
                params={},
            )
            assert rows_count_resp["response"]["numFound"] == len(documents)
            solr_connection.get_admin_client().delete_all_collections()

    @pytest.mark.asyncio
    async def test_index_nonexistent_collection_redirect(self, solr_connection):
        """Test redirect when collection doesn't exist"""
        app = create_app()
        with TestClient(app) as test_router:
            index_data_request = IndexDataRequest(data=documents)
            with patch.dict(
                test_router.app.state.config, {"solr_config": MockSolrConfig()}
            ):
                response = test_router.post(
                    "/collections/3212", content=index_data_request.model_dump_json()
                )

            assert response.status_code == 404
            assert "Collection not found" in response.text

    @pytest.mark.asyncio
    async def test_index_data_internal_error(self, solr_connection):
        """Test exception handling during indexing"""
        app = create_app()
        with TestClient(app) as test_router:
            create_request = CreatecollectionRequest(
                server_id="error_collection", shards=1, replicas=1
            )
            with patch.dict(
                test_router.app.state.config, {"solr_config": MockSolrConfig()}
            ):
                test_router.post(
                    "/collections", content=create_request.model_dump_json()
                )

            index_data_request = IndexDataRequest(data=[{}])
            response = test_router.post(
                "/collections/1234", content=index_data_request.model_dump_json()
            )

            assert response.status_code == 500
            assert "Internal server error" in response.text
