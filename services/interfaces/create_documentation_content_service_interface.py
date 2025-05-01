from abc import ABC, abstractmethod


class CreateDocumentationContentServiceInterface(ABC):
    @abstractmethod
    def __init__() -> None:
        pass

    @abstractmethod
    async def create_document_content_from_messages(
        self, documents: list[str], server_id: str
    ) -> list[str]:
        pass
