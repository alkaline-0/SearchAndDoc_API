from sentence_transformers import SentenceTransformer

from db.helpers.interfaces.sentence_transformer_interface import SentenceTransformerInterface


class STSentenceTransformer(SentenceTransformerInterface):
    def __init__(self, model_name: str, device: str) -> None:
        self._model = SentenceTransformer(model_name, device=device)

    def encode(self, sentences: list[str], **kwargs):
        return self._model.encode(sentences, **kwargs)
