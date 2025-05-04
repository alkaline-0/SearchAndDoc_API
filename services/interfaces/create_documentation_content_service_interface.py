from abc import ABC, abstractmethod
from logging import Logger


class CreateDocumentationContentServiceInterface(ABC):
    @abstractmethod
    def __init__(self, logger: Logger) -> None:
        pass

    @abstractmethod
    async def create_document_content_from_messages(
        self, documents: list[dict], server_id: str
    ) -> str:
        pass
