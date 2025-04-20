class SolrError(Exception):
    """Base exception for Solr operations."""
    pass

class SolrConnectionError(SolrError):
    """Raised when connection to Solr fails."""
    pass

class SolrValidationError(SolrError):
    """Raised when validation fails."""
    pass