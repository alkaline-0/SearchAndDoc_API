from abc import ABC, abstractmethod
from typing import List


class SentenceTransformerInterface(ABC):
    @abstractmethod
    def encode(self, sentences: List[str], **kwargs):
        pass