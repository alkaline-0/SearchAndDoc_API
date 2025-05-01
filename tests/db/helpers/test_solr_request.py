import pytest

from db.helpers.solr_request import make_solr_request
from db.solr_utils.solr_config import SolrConfig
from db.solr_utils.solr_exceptions import SolrError


def test_make_solr_request_catch_general_exception():
    with pytest.raises(SolrError) as excinfo:
        cfg_wrong_password = SolrConfig(PASSWORD="wrong")
        make_solr_request(
            cfg=cfg_wrong_password, params={}, url=cfg_wrong_password.BASE_URL
        )

        assert "Unexpected error occurred:" in str(excinfo.value)
