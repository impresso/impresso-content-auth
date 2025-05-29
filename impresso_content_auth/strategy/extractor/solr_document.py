"""
Strategy module for extracting tokens from Solr documents.
"""

import logging
import re
from typing import Callable, Generic, Optional, TypeVar, cast

from starlette.requests import Request

from impresso_content_auth.service.solr import SolrService
from impresso_content_auth.strategy.extractor.base import TokenExtractorStrategy

T = TypeVar("T")
logger = logging.getLogger(__name__)


class SolrDocumentExtractor(Generic[T], TokenExtractorStrategy[T]):
    """
    A strategy that extracts tokens from Solr documents based on request parameters.

    This extractor:
    1. Extracts a document ID from the request URL using the provided extractor function
    2. Queries Solr to retrieve the document
    3. Extracts the token from the document using a provided extractor function
    """

    def __init__(
        self,
        solr_service: SolrService,
        collection: str,
        id_extractor_func: Callable[[Request], Optional[str]],
        field: str,
    ):
        """
        Initialize the Solr document extractor.

        Args:
            solr_service: The Solr service to use for queries
            collection: The Solr collection to query
            id_extractor_func: Function to extract document ID from the request URL
            field: The field to extract from the Solr document
        """
        self.solr_service = solr_service
        self.collection = collection
        self.id_extractor_func = id_extractor_func
        self.field = field

    async def __call__(self, request: Request) -> Optional[T]:
        """
        Extract a token from a Solr document based on the request.

        Args:
            request: The HTTP request

        Returns:
            The extracted token or None if not found
        """
        # Extract document ID from the request URL
        doc_id = self.id_extractor_func(request)
        if not doc_id:
            logger.debug("No document ID extracted from request URL")
            return None

        try:
            # Query Solr for the document
            query = f"id:{doc_id}"
            response = self.solr_service.search(
                collection=self.collection,
                q=query,
                fields=[self.field],
                rows=1,
            )

            # Extract document from response
            docs = response.get("response", {}).get("docs", [])
            if not docs:
                logger.debug("No document found with ID '%s'", doc_id)
                return None

            # Extract token from document
            document = docs[0]
            return cast(T, document.get(self.field, None))

        except (ConnectionError, TimeoutError) as e:
            logger.error("Network error while querying Solr: %s", str(e))
            raise
        except ValueError as e:
            logger.error("Error processing Solr response: %s", str(e))
            raise

    def __str__(self) -> str:
        """Return a string representation of the extractor."""
        return f"SolrDocumentExtractor(solr_base_url={self.solr_service.base_url}, collection={self.collection}, field={self.field})"


def extract_id_from_x_original_uri(request: Request) -> Optional[str]:
    """
    Extract document ID from the `X-Original-URI` header of the request.

    This function extracts the document ID from URLs following the pattern:
    /foo/bar/baz/img-1.jpg -> img-1
    /foo/bar/baz/audio-1.mp3 -> audio-1

    Args:
        request: The HTTP request

    Returns:
        The extracted document ID or None if not found
    """
    path = request.headers.get("x-original-uri", "")
    if not path:
        logger.debug("No 'x-original-uri' header found in request")
        return None

    # Match the last path component and extract the ID before the file extension
    match = re.search(r"/([^/]+)\.[\w]+$", path)
    if not match:
        logger.debug("Could not extract ID from URL path: %s", path)
        return None

    # Extract the filename without extension and remove any suffix after the last dash
    id_match = match.group(1)

    return id_match
