from abc import ABC, abstractmethod


class SentenceTransformerInterface(ABC):
    @abstractmethod
    def encode(self, sentences: list[str], **kwargs):
        pass
