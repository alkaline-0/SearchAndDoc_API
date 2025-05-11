from unittest.mock import call, patch

import pytest
import requests

from db.config.solr_config import SolrConfig
from db.data_access.solr_http_client import SolrHttpClient
from db.utils.exceptions import SolrConnectionError, SolrError
from utils.get_logger import get_logger


def test_make_solr_request_catch_general_exception():
    with pytest.raises(SolrError) as excinfo:

        cfg_wrong_password = SolrConfig(PASSWORD="wrong")
        logger = get_logger()
        with patch.object(logger, "error") as mock_logger:
            http_client = SolrHttpClient(cfg=cfg_wrong_password, logger=logger)
            http_client.send_request(
                params={},
                url=cfg_wrong_password.BASE_URL,
            )
        mock_logger.error.assert_has_calls(
            [call(excinfo.value), call(stack_info=True), call(exc_info=True)]
        )
        assert "Unexpected error occurred:" in str(excinfo.value)


def test_make_solr_request_catch_solr_connection_exception():
    with pytest.raises(SolrError) as excinfo:

        cfg_wrong_password = SolrConfig(PASSWORD="wrong")
        logger = get_logger()
        with (
            patch.object(logger, "error") as mock_logger,
            patch.object(requests, "get") as requests_mock,
        ):
            e = SolrConnectionError("connection failed")
            requests_mock.return_value = e
            requests_mock.side_effect = e
            http_client = SolrHttpClient(cfg=cfg_wrong_password, logger=logger)
            http_client.send_request(
                params={},
                url=cfg_wrong_password.BASE_URL,
            )
        mock_logger.error.assert_has_calls(
            [call(e), call(stack_info=True), call(exc_info=True)]
        )
        assert "Unexpected error occurred:" in str(excinfo.value)
