from unittest.mock import MagicMock, call, patch

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from db.services import collection_admin_service
from db.utils.exceptions import SolrError
from routers.create_collection_router import (CreatecollectionRequest)
from tests.db.mocks.mock_solr_config import MockSolrConfig
from utils.get_logger import get_logger


class TestCreateCollectionRouter:
  @pytest.mark.asyncio
  async def test_create_collection_successfully(self, solr_connection):
    app = create_app()
    with TestClient(app) as test_router:
      request_params = CreatecollectionRequest(server_id="1234", shards=1, replicas=1)
      with (patch.dict(test_router.app.state.config, {"solr_config": MockSolrConfig()})):          
          response = test_router.post("/create-collection", content=request_params.model_dump_json())
          
          admin_client = solr_connection.get_admin_client()

      assert response.status_code == 201
      assert response.json() == {"message": f"Collection 1234 created"}
      assert  admin_client.collection_exist("1234") is True
   
  @pytest.mark.asyncio
  async def test_create_collection_already_exists(self, solr_connection):
    app = create_app()
    with TestClient(app) as test_router:
        request_params = CreatecollectionRequest(server_id="5678", shards=1, replicas=1)
        with patch.dict(test_router.app.state.config, {"solr_config": MockSolrConfig()}):
            test_router.post("/create-collection", content=request_params.model_dump_json())
            response = test_router.post("/create-collection", content=request_params.model_dump_json())
        assert response.status_code == 400
        assert response.json() == {"detail": "Collection already exists"}
        solr_connection.get_admin_client().delete_all_collections()

  @pytest.mark.asyncio
  async def test_create_collection_internal_error(self, solr_connection):
      app = create_app()
      with TestClient(app) as test_router:
          request_params = CreatecollectionRequest(server_id="1234", shards=1, replicas=1)
          with (patch.dict(test_router.app.state.config, {"solr_config": MockSolrConfig()}),
                patch("db.services.collection_admin_service.CollectionAdminService.create_collection", side_effect=SolrError())):
                    response = test_router.post("/create-collection", content=request_params.model_dump_json())
                    admin_client = solr_connection.get_admin_client()

          assert response.status_code == 500
          assert response.json() == {"detail": "Internal server error"}
          assert admin_client.collection_exist("1234") is False
