# interfaces/http_client_interface.py

from abc import ABC, abstractmethod


class SolrHttpClientInterface(ABC):
    @abstractmethod
    def send_request(self, url: str, params: dict) -> dict:
        pass
