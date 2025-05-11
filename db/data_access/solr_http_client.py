# services/solr_http_client.py

import json
from logging import Logger
from typing import Any

import pysolr
import requests
from requests.auth import HTTPBasicAuth

from db.config.solr_config import SolrConfig
from db.data_access.interfaces.http_client_interface import SolrHttpClientInterface
from db.utils.exceptions import SolrConnectionError, SolrError


class SolrHttpClient(SolrHttpClientInterface):
    def __init__(self, cfg: SolrConfig, logger: Logger):
        self.cfg = cfg
        self.logger = logger

    def send_request(self, url: str, params: dict[str, Any]) -> dict:
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        basic = HTTPBasicAuth(self.cfg.USER_NAME, self.cfg.PASSWORD)

        try:
            response = requests.get(
                url=url,
                params=params,
                headers=headers,
                auth=basic,
            )
            response.raise_for_status()
            return json.loads(pysolr.force_unicode(response.content))

        except requests.exceptions.RequestException as error:
            self.logger.error(error, stack_info=True, exc_info=True)
            raise SolrConnectionError(error)
        except Exception as error:
            self.logger.error(error, stack_info=True, exc_info=True)
            raise SolrError(error)
