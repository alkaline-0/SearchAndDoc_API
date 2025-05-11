from sentence_transformers import util

from db.utils.interfaces.rerank_strategy_interface import RerankStrategy


class CosineSimilarityReranker(RerankStrategy):
    def rerank(self, query_embedding, candidate_embeddings, docs) -> list[dict]:
        scores = util.cos_sim(query_embedding, candidate_embeddings)[0].cpu().tolist()
        return sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
