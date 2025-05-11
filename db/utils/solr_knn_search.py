from datetime import datetime

from db.utils.interfaces.retrieval_strategy_interface import RetrievalStrategy


class SolrKnnSearch(RetrievalStrategy):
    def __init__(self, solr_client, cfg, logger):
        self.solr_client = solr_client
        self.cfg = cfg
        self._logger = logger

    def retrieve(
        self, embedding: list, total_rows: int, start_date: datetime, end_date: datetime
    ) -> list:
        """Ray-optimized parallel fetching for large result sets"""
        chunk_size = 5000
        futures = []
        knn_q = "{!knn f=bert_vector}" + str([float(w) for w in embedding[0]])
        for start in range(0, total_rows, chunk_size):
            actual_rows = min(chunk_size, total_rows - start)
            batch_res = self._fetch_results_in_chunks_with_date(
                q=knn_q,
                start=start,
                rows_count=actual_rows,
                start_date=start_date,
                end_date=end_date,
            )

            if len(batch_res) > 0:
                futures.append(batch_res)

        return futures

    def _fetch_results_in_chunks_with_date(
        self,
        start: int,
        q: str,
        rows_count: int,
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> list:
        """Fetch search results in paginated chunks with date filtering."""
        try:
            solr_date_format = "%Y-%m-%dT%H:%M:%SZ"

            if not start_date or not end_date:
                return self._fetch_results_in_chunks(
                    start=start, q=q, rows_count=rows_count
                )

            params = {
                "q": q,
                "start": start,
                "fl": "message_id, message_content, author_id, channel_id, created_at",
                "rows": rows_count,
                "sort": "score desc, message_id asc",
                "fq": f"(created_at:[{start_date.strftime(solr_date_format)} TO {end_date.strftime(solr_date_format)}] OR (*:* NOT created_at:[* TO *]))",
            }
            params = {k: v for k, v in params.items() if v is not None}

            query_exec = self.solr_client.search(**params)
            return query_exec.docs
        except Exception as e:
            self._logger.error(
                f"Failed to fetch chunk {start}-{start+rows_count}: {str(e)}",
                exc_info=True,
                stack_info=True,
            )
            raise

    def _fetch_results_in_chunks(self, start: int, q: str, rows_count: int) -> list:
        try:
            params = {
                "q": q,
                "start": start,
                "fl": "message_id, message_content, author_id, channel_id",
                "rows": rows_count,
                "sort": "score desc, message_id asc",
            }
            query_exec = self.solr_client.search(**params)
            return query_exec.docs
        except Exception as e:
            self._logger.error(e, stack_info=True, exc_info=True)
            raise e
