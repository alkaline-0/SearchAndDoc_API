from sentence_transformers import SentenceTransformer

from db.solr_utils.sentence_transformer_interface import SentenceTransformerInterface


class STSentenceTransformer(SentenceTransformerInterface):
    def __init__(self, model_name: str):
        self._model = SentenceTransformer(model_name)

    def encode(self, sentences: list[str], **kwargs):
        return self._model.encode(sentences, **kwargs)
