from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class SolrClientInterface(ABC):
    @abstractmethod
    def add(self, documents: list[dict[str, Any]], soft_commit: bool) -> Any:
        pass

    @abstractmethod
    def search(self, *args, **kwargs) -> Any:
        pass
