from db.utils.exceptions import SolrValidationError
from db.utils.interfaces.sentence_transformer_interface import (
    SentenceTransformerInterface,
)
from models.base_model import BaseModel


class IndexingCollectionModel(BaseModel):
    def __init__(
        self,
        cfg,
        collection_url: str,
        retriever_model: SentenceTransformerInterface,
    ):
        _conn_obj = super().get_connection_object(cfg)

        self._indexing_client = _conn_obj.get_index_client(
            collection_url=collection_url, retriever_model=retriever_model
        )

    def index_data(self, documents: list[dict], soft_commit: bool = True) -> None:
        if not len(documents):
            raise SolrValidationError("Data to index cannot be empty")

        self._indexing_client.index_data(data=documents, soft_commit=soft_commit)
