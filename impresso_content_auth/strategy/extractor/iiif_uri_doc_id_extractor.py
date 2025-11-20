"""Document ID extractor from IIIF URI in x-original-uri header."""

import logging
from typing import Optional

from starlette.requests import Request

from impresso_content_auth.strategy.extractor.base import TokenExtractorStrategy
from impresso_content_auth.strategy.extractor.solr_document import (
    extract_id_from_x_original_uri_with_iiif,
)

logger = logging.getLogger(__name__)


class IIIFUriDocIdExtractor(TokenExtractorStrategy[Optional[str]]):
    """
    Extractor that gets document ID from IIIF URI in x-original-uri header.

    Extracts the document ID from the x-original-uri header, handling IIIF paths.
    """

    async def __call__(self, request: Request) -> Optional[str]:
        """
        Extract document ID from IIIF URI in x-original-uri header.

        Args:
            request: The incoming HTTP request

        Returns:
            The document ID if successfully extracted, None otherwise
        """
        try:
            doc_id = extract_id_from_x_original_uri_with_iiif(request)
            if doc_id:
                logger.debug("Successfully extracted document ID from IIIF URI: %s", doc_id)
            else:
                logger.warning("Failed to extract document ID from IIIF URI")
            return doc_id
        except Exception as e:
            logger.error("Error extracting document ID from IIIF URI: %s", str(e))
            return None

    def __str__(self) -> str:
        """Return a string representation of the extractor."""
        return "IIIFUriDocIdExtractor()"
