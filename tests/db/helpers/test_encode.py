import numpy as np
import ray

from db.helpers.encode import create_embeddings
from tests.db.conftest import RERANK_MODEL, RETRIEVER_MODEL


def test_normalize_create_embeddings_successfully():
    sentences = [
        "The weather is lovely today.",
        "It's so sunny outside!",
        "He drove to the stadium.",
    ]
    normalized = ray.get(
        create_embeddings.remote(
            model=RERANK_MODEL, sentences=sentences, normalize_embeddings=True
        )
    )
    norms = [np.linalg.norm(vec) for vec in normalized]
    # All norms should be very close to 1
    assert all(abs(n - 1.0) < 1e-6 for n in norms)


def test_create_none_normalized_emeddings_successfully():
    sentences = [
        "The weather is lovely today.",
        "It's so sunny outside!",
        "He drove to the stadium.",
    ]
    embeddings = ray.get(
        create_embeddings.remote(
            model=RETRIEVER_MODEL, sentences=sentences, normalize_embeddings=False
        )
    )
    norms = [np.linalg.norm(vec) for vec in embeddings]
    assert any(abs(n - 1.0) > 1e-6 for n in norms) is True
