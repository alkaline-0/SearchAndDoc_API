class SolrError(Exception):
    """Base exception for Solr operations."""


class SolrConnectionError(SolrError):
    """Raised when connection to Solr fails."""


class SolrValidationError(SolrError):
    """Raised when validation fails."""
