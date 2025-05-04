import pytest

from db.config.solr_config import SolrConfig
from db.utils.exceptions import SolrError
from db.utils.request import request


def test_make_solr_request_catch_general_exception():
    with pytest.raises(SolrError) as excinfo:
        cfg_wrong_password = SolrConfig(PASSWORD="wrong")
        request(cfg=cfg_wrong_password, params={}, url=cfg_wrong_password.BASE_URL)

        assert "Unexpected error occurred:" in str(excinfo.value)
