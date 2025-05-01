import inspect
import json
from typing import Any

import pysolr
import requests
from requests.auth import HTTPBasicAuth

from db.config.solr_config import SolrConfig
from db.utils.exceptions import SolrConnectionError, SolrError


def request(cfg: SolrConfig, params: dict[str, Any], url: str) -> dict:
    """Makes HTTP request to Solr and handles response.

    Args:
        params: Request parameters

    Returns:
        Python object containing parsed JSON response with the result of the request

    Raises:
        requests.exceptions.HTTPError: If request fails
        Exception: For other unexpected errors
    """
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    basic = HTTPBasicAuth(cfg.USER_NAME, cfg.PASSWORD)
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
        caller_frame = inspect.getouterframes(inspect.currentframe(), 2)
        print(f"Solr request failed originating from {caller_frame[1][3]}: {error}")
        raise SolrConnectionError(error)
    except Exception as error:
        print(f"Unexpected error occurred: {error}")
        raise SolrError(error)
