from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from db.utils.exceptions import SolrError
from db.utils.request import request
from routers.create_collection_router import CreatecollectionRequest
from routers.create_document_router import CreateDocumentRequest
from routers.index_data_router import IndexDataRequest
from tests.db.mocks.mock_solr_config import MockSolrConfig
from tests.fixtures.test_data.fake_messages import documents
from utils.get_logger import get_logger


class TestCreateDocumentRouter:
  @pytest.mark.asyncio
  async def test_create_document_successfully(self, solr_connection):
      app = create_app()
      with TestClient(app) as test_router:
          request_params = CreatecollectionRequest(
              server_id="5678", shards=1, replicas=1
          )
          with patch.dict(
              test_router.app.state.config, {"solr_config": MockSolrConfig()}
          ):
              test_router.post(
                  "/create-collection", content=request_params.model_dump_json()
              )
              index_data_request = IndexDataRequest(server_id="5678", data=documents)
              test_router.post(
                  "/index-data", content=index_data_request.model_dump_json()
              )
              create_document_params = CreateDocumentRequest(
                server_id="5678",
                topic="web application project",
                start_date="2025-04-13T13:24:00Z",
                end_date="2025-04-19T13:24:00Z"
              )
              
              response = test_router.post("/create-document", content=create_document_params.model_dump_json())
              

          assert response.status_code == 200
          assert response.text is not None
          assert all(item in response.text for item in ["Overview", "Features", "Next Steps"])
          solr_connection.get_admin_client().delete_all_collections()
  
  @pytest.mark.asyncio
  async def test_invalid_date_format(self, solr_connection):
    """Test bad date formatting handling"""
    app = create_app()
    with TestClient(app) as test_router:
        doc_request = CreateDocumentRequest(
            server_id="5678",
            topic="test",
            start_date="2025-04-19T13:24:00Z",  # Invalid format
            end_date="2025-04-13T13:24:00Z"
        )
        with patch.dict(test_router.app.state.config, {"solr_config": MockSolrConfig()}):
            response = test_router.post("/create-document", content=doc_request.model_dump_json())
        
        assert response.status_code == 400
        assert "Failed to create document. Invalid input or server error." in response.text
        solr_connection.get_admin_client().delete_all_collections()


  @pytest.mark.asyncio
  async def test_nonexistent_collection(self, solr_connection):
    """Test document creation for missing collection"""
    app = create_app()
    with TestClient(app) as test_router:
        doc_request = CreateDocumentRequest(
            server_id="missing_collection",
            topic="test",
            start_date="2025-04-13T13:24:00Z",
            end_date="2025-04-19T13:24:00Z"
        )
        with patch.dict(test_router.app.state.config, {"solr_config": MockSolrConfig()}):
            response = test_router.post("/create-document", content=doc_request.model_dump_json())
        
        assert response.status_code == 400
        assert "Invalid input or server error" in response.text
        solr_connection.get_admin_client().delete_all_collections()


  @pytest.mark.asyncio
  async def test_solr_error_propagation(self, solr_connection):
    """Test Solr exception handling"""
    app = create_app()
    with TestClient(app) as test_router:
        doc_request = CreateDocumentRequest(
            server_id="5678",
            topic="test",
            start_date="2025-04-20T13:24:00Z",
            end_date="2025-04-27T13:24:00Z"
        )
        with patch.dict(test_router.app.state.config, {"solr_config": MockSolrConfig()}):
            # Create collection first
            coll_request = CreatecollectionRequest(server_id="5678", shards=1, replicas=1)
            test_router.post("/create-collection", content=coll_request.model_dump_json())
                  
            with patch.object(solr_connection, "_logger") as mock_logger:
              response = test_router.post("/create-document", 
                                        content=doc_request.model_dump_json())
                
        assert response.status_code == 500
        assert "Search failed" in response.text
       

                