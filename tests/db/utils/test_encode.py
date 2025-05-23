import numpy as np
import ray

from db.utils.encode import create_embeddings


def test_create_embeddings_successfully_with_normalize(rerank_model):
    sentences = [
        "The weather is lovely today.",
        "It's so sunny outside!",
        "He drove to the stadium.",
    ]
    normalized = ray.get(
        create_embeddings.remote(
            model=rerank_model, sentences=sentences, normalize_embeddings=True
        )
    )
    norms = [np.linalg.norm(vec) for vec in normalized]
    # All norms should be very close to 1
    assert all(abs(n - 1.0) < 1e-6 for n in norms)


def test_create_emeddings_successfully_without_normalize(retriever_model):
    sentences = [
        "The weather is lovely today.",
        "It's so sunny outside!",
        "He drove to the stadium.",
    ]
    embeddings = ray.get(
        create_embeddings.remote(
            model=retriever_model, sentences=sentences, normalize_embeddings=False
        )
    )
    norms = [np.linalg.norm(vec) for vec in embeddings]
    assert any(abs(n - 1.0) > 1e-6 for n in norms) is True
