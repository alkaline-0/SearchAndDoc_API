import ray

from db.helpers.sentence_transformer_impl import STSentenceTransformer


@ray.remote(num_returns=1)
def create_embeddings(
    sentences: list[str], model: STSentenceTransformer, normalize_embeddings: bool
):
    if normalize_embeddings:
        return model.encode(sentences, normalize_embeddings=True)
    else:
        return model.encode(sentences)
